"""Motor de análisis adaptativo basado en evidencia académica ya registrada.

No crea actividades ni modifica notas. Su responsabilidad es explicar qué tema
requiere apoyo y qué dificultad conviene usar; la generación y publicación se
mantienen en servicios y rutas docentes separados.
"""
from collections import defaultdict
from typing import Any, Dict, List

from services import db_service


def _percentage(record: Dict[str, Any]) -> float:
    """Normaliza una nota a 0..100 sin asumir que todas usan la misma escala."""
    value = record.get('percentage')
    if value is not None:
        try:
            return max(0.0, min(100.0, float(value)))
        except (TypeError, ValueError):
            pass
    try:
        score = float(record.get('score') or 0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, score * 5 if score <= 20 else score))


def _risk_label(payload: Dict[str, Any]) -> str:
    return str(payload.get('risk_level') or payload.get('risk_level_label') or 'UNKNOWN').upper()


def _difficulty(risk_level: str, average: float) -> str:
    if risk_level in {'HIGH', 'ALTO'} or average < 50:
        return 'easy'
    if risk_level in {'MEDIUM', 'MEDIO'} or average < 75:
        return 'medium'
    return 'hard'


def _trend(values: List[float]) -> str:
    if len(values) < 2:
        return 'insufficient_data'
    recent = sum(values[: min(3, len(values))]) / min(3, len(values))
    previous_values = values[3:6]
    if not previous_values:
        return 'stable'
    previous = sum(previous_values) / len(previous_values)
    if recent >= previous + 8:
        return 'improving'
    if recent <= previous - 8:
        return 'declining'
    return 'stable'


def build_adaptive_learning_profile(student_id: int) -> Dict[str, Any]:
    """Combina notas, evaluaciones, errores en juegos, tendencia y predicción ML.

    ``weak_topics`` solo incluye temas sustentados por un registro existente. Si
    faltan evidencias por tema, se devuelve una recomendación general en vez de
    inventar una debilidad.
    """
    from services.student_learning_service import build_student_risk_payload

    student_id = int(student_id)
    student = db_service.fetch_student_by_id(student_id) or {'id': student_id, 'grade': 5}
    grade = int(student.get('grade') or 5)
    topics = db_service.fetch_topics_for_grade(grade) or []
    topics_by_id = {int(item['id']): item for item in topics if item.get('id') is not None}
    notes = db_service.fetch_student_notes(student_id) or []
    assessments = db_service.fetch_student_assessment_attempts(student_id) or []
    games = db_service.fetch_student_game_attempts(student_id) or []
    risk = build_student_risk_payload(student_id) or {}
    evidence = defaultdict(lambda: {'topic_id': None, 'title': '', 'severity': 0.0, 'events': 0, 'reasons': []})

    def add(topic_id: Any, title: Any, severity: float, reason: str) -> None:
        try:
            normalized_id = int(topic_id) if topic_id is not None else None
        except (TypeError, ValueError):
            normalized_id = None
        resolved = topics_by_id.get(normalized_id, {})
        resolved_title = str(title or resolved.get('title') or '').strip()
        if not resolved_title:
            return
        key = normalized_id if normalized_id is not None else resolved_title.lower()
        item = evidence[key]
        item['topic_id'] = normalized_id
        item['title'] = resolved_title
        item['severity'] += max(0.0, severity)
        item['events'] += 1
        if reason not in item['reasons']:
            item['reasons'].append(reason)

    for note in notes:
        percent = _percentage(note)
        if percent < 75:
            add(note.get('topic_id'), note.get('topic'), 100 - percent, f"resultado registrado de {round(percent)}%")
    for attempt in assessments:
        total = int(attempt.get('total_questions') or 0)
        correct = int(attempt.get('correct_answers') or 0)
        failed = max(0, total - correct)
        if not failed:
            continue
        severity = (failed / total * 100) if total else (100 - _percentage(attempt))
        for title in attempt.get('reinforce_topics') or []:
            matching = next((item for item in topics if str(item.get('title', '')).lower() == str(title).lower()), {})
            add(matching.get('id'), title, severity, f"{failed} respuestas incorrectas en evaluación")
    for attempt in games:
        if attempt.get('is_correct') is False:
            topic = topics_by_id.get(int(attempt.get('topic_id') or 0), {})
            add(attempt.get('topic_id'), topic.get('title'), 35.0, 'error registrado en juego')

    weak_topics = sorted(evidence.values(), key=lambda item: (-item['severity'], -item['events'], item['title'].lower()))[:3]
    weak_topics = [{'topic_id': item['topic_id'], 'title': item['title'], 'evidence_count': item['events'], 'reasons': item['reasons']} for item in weak_topics]
    note_values = [_percentage(note) for note in notes]
    average = round(sum(note_values) / len(note_values), 2) if note_values else None
    risk_level = _risk_label(risk)
    recommended_difficulty = _difficulty(risk_level, average if average is not None else 70.0)
    primary = weak_topics[0] if weak_topics else None
    recommended_activity: Dict[str, Any] = {'type': 'continue_learning', 'title': 'Continúa con tus actividades publicadas', 'message': 'Aún no hay suficiente evidencia por tema para personalizar una práctica.', 'topic_id': None, 'game_id': None}
    if primary:
        materials = db_service.fetch_all_materials_for_student(student_id, grade) or []
        material = next((item for item in materials if item.get('topic_id') == primary['topic_id']), None)
        published = db_service.fetch_published_ai_games_for_topic(primary['topic_id']) or []
        if published:
            recommended_activity = {'type': 'published_ai_game', 'title': published[0].get('title') or f"Práctica de {primary['title']}", 'message': f"Práctica publicada para reforzar {primary['title']}.", 'topic_id': primary['topic_id'], 'game_id': published[0].get('id')}
        elif material:
            recommended_activity = {'type': 'review_material', 'title': material.get('title') or primary['title'], 'message': f"Repasa el material docente de {primary['title']} mientras el docente revisa una práctica.", 'topic_id': primary['topic_id'], 'material_id': material.get('id'), 'game_id': None}

    return {'student_id': student_id, 'risk_level': risk_level, 'risk_probability': risk.get('probability'), 'weak_topics': weak_topics, 'recommended_difficulty': recommended_difficulty, 'recommended_activity': recommended_activity, 'trend': _trend(note_values), 'evidence_summary': {'notes': len(notes), 'assessment_attempts': len(assessments), 'game_attempts': len(games), 'average_percentage': average}}
