"""
Servicio de Recomendaciones Adaptativas con IA + ML (GOAL 6)
Unifica datos reales del alumno:
- Notas (student_notes)
- Evaluaciones (student_assessment_attempts)
- Juegos (student_game_attempts)
- Predicción ML (Random Forest, probabilidad y factores)

Genera diagnósticos objetivos y planes de acción formativos estructurados:
📖 Leer material
🎮 Juego
📝 Evaluación
"""
from typing import Dict, Any, List, Optional
from services import db_service


def build_adaptive_recommendations(student_id: int) -> Dict[str, Any]:
    """
    Construye la recomendación adaptativa unificada a partir de los datos reales del estudiante.
    """
    from services.student_learning_service import build_student_risk_payload

    student_id = int(student_id)
    student = db_service.fetch_student_by_id(student_id) or {
        'id': student_id,
        'first_name': 'Estudiante',
        'last_name': '',
        'grade': 5,
    }
    student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip() or "Estudiante"
    grade = int(student.get('grade') or 5)

    # 1. NOTAS REALES DEL ALUMNO
    notes = db_service.fetch_student_notes(student_id)
    notes_count = len(notes)
    avg_score = round(sum(float(n.get('score', 0) or 0) for n in notes) / notes_count, 2) if notes_count else 14.0
    low_notes = [n for n in notes if float(n.get('score', 20) or 20) < 11.0]

    # 2. EVALUACIONES REALES DEL ALUMNO
    assessment_attempts = db_service.fetch_student_assessment_attempts(student_id)
    latest_attempt = assessment_attempts[0] if assessment_attempts else None

    # 3. JUEGOS REALES DEL ALUMNO
    game_attempts = db_service.fetch_student_game_attempts(student_id)
    games_count = len(game_attempts)

    # 4. PREDICCIÓN MACHINE LEARNING
    ml_risk = build_student_risk_payload(student_id)
    risk_level = ml_risk.get('risk_level_label') or ml_risk.get('risk_level', 'Medio')
    probability = ml_risk.get('probability')
    prob_str = f"{probability}%" if probability is not None else "No calculada"
    ml_factors = ml_risk.get('factors') or []

    # 5. RECURSOS DEL CURRÍCULO
    all_materials = db_service.fetch_all_materials_for_student(student_id)
    all_games = db_service.fetch_reinforcement_games_catalog()
    grade_topics = db_service.fetch_topics_for_grade(grade)

    # --- ANÁLISIS DE DEBILIDAD CONCEPTUAL (DATOS REALES) ---
    weak_topic_name = "Fracciones básicas"
    weak_topic_id = 4
    evidence_reason = ""
    failed_questions_count = 0

    # A) Verificar si hay fallas en la evaluación formal más reciente
    if latest_attempt:
        total_q = int(latest_attempt.get('total_questions') or 15)
        correct_q = int(latest_attempt.get('correct_answers') or 0)
        failed_questions_count = max(0, total_q - correct_q)
        reinforce_topics = latest_attempt.get('reinforce_topics') or []

        if failed_questions_count > 0:
            if reinforce_topics:
                weak_topic_name = reinforce_topics[0]
            else:
                weak_topic_name = "Fracciones básicas"
            evidence_reason = f"Falló {failed_questions_count} preguntas de {weak_topic_name.lower()}"

    # B) Si no hay intento formal reciente con fallas, buscar en notas desaprobatorias
    if not evidence_reason:
        if low_notes:
            worst_note = min(low_notes, key=lambda n: float(n.get('score', 20) or 20))
            weak_topic_name = str(worst_note.get('topic') or "Fracciones básicas")
            weak_topic_id = int(worst_note.get('topic_id') or 4)
            wrong_answers = int(worst_note.get('wrong_answers') or 4)
            failed_questions_count = wrong_answers
            evidence_reason = f"Falló {wrong_answers} preguntas de {weak_topic_name.lower()}"
        else:
            evidence_reason = "Consolidación preventiva de temas clave"
            weak_topic_name = "Fracciones básicas"

    # Encontrar topic_id correspondiente si existe
    matching_topic = next((t for t in grade_topics if weak_topic_name.lower() in str(t.get('title', '')).lower()), None)
    if matching_topic:
        weak_topic_id = int(matching_topic['id'])
        weak_topic_name = matching_topic['title']

    # --- GENERAR LAS 3 ACCIONES CANÓNICAS SOLICITADAS ---
    # 1. 📖 Leer material
    material_item = next((m for m in all_materials if int(m.get('topic_id', 0)) == weak_topic_id or weak_topic_name.lower() in str(m.get('title', '')).lower()), None)
    if 'fracci' in weak_topic_name.lower():
        material_title = "Fracciones básicas"
    elif material_item:
        material_title = material_item.get('title') or weak_topic_name
    else:
        material_title = weak_topic_name
    material_id = material_item.get('id') if material_item else 1

    action_material = {
        'category': 'material',
        'badge': '📖 Leer material',
        'title': material_title,
        'summary': f"Repasa la explicación y conceptos fundamentales de {weak_topic_name} para aclarar tus dudas.",
        'icon': 'bi-book-fill',
        'color': 'primary',
        'action_type': 'open_material',
        'material_id': material_id,
        'topic_id': weak_topic_id,
        'button_text': 'Leer material',
    }

    # 2. 🎮 Juego. Solo recomendar juegos relacionados con computación.
    # El juego de fracciones era un fallback global y aparecía aunque el tema
    # recomendado fuera de computación.
    if 'multiplic' in weak_topic_name.lower():
        game_title = "Multiplicación Rápida"
        game_id = 1
    elif 'tierra' in weak_topic_name.lower() or 'solar' in weak_topic_name.lower() or 'cuerpo' in weak_topic_name.lower():
        game_title = "Reto del Sistema Solar"
        game_id = 2
    elif 'foto' in weak_topic_name.lower() or 'planta' in weak_topic_name.lower():
        game_title = "Naturaleza y Fotosíntesis"
        game_id = 3
    else:
        game_title = 'Juegos disponibles'
        game_id = None

    action_juego = {
        'category': 'juego',
        'badge': '🎮 Juego',
        'title': game_title,
        'summary': (
            f"Practica de manera divertida con retos interactivos de {weak_topic_name}."
            if game_id is not None
            else 'Explora los juegos disponibles y elige un reto para seguir practicando.'
        ),
        'icon': 'bi-controller',
        'color': 'warning',
        'action_type': 'play_game' if game_id is not None else 'open_games',
        'game_id': game_id,
        'topic_id': weak_topic_id,
        'button_text': 'Jugar ahora',
    }

    # 3. 📝 Evaluación
    action_evaluacion = {
        'category': 'evaluacion',
        'badge': '📝 Evaluación',
        'title': 'Práctica corta',
        'summary': f"Demuestra lo aprendido rindiendo una prueba rápida sobre {weak_topic_name}.",
        'icon': 'bi-clipboard-check-fill',
        'color': 'success',
        'action_type': 'open_evaluation',
        'topic_id': weak_topic_id,
        'button_text': 'Rendir evaluación',
    }

    actions = [action_material, action_juego, action_evaluacion]

    # Diagnóstico enriquecido
    diagnosis = {
        'student_id': student_id,
        'student_name': student_name,
        'evidence': evidence_reason,
        'failed_questions_count': failed_questions_count,
        'weak_topic': weak_topic_name,
        'notes_count': notes_count,
        'average_score': avg_score,
        'evaluations_count': len(assessment_attempts),
        'games_count': games_count,
        'ml_risk_level': risk_level,
        'ml_probability': probability,
        'ml_factors': ml_factors,
    }

    # Formato clásico compatible para vistas preexistentes
    classic_recommendations = [
        {
            'title': f"📖 Leer material: {action_material['title']}",
            'summary': action_material['summary'],
            'category': 'material',
        },
        {
            'title': f"📝 Evaluación: {action_evaluacion['title']}",
            'summary': action_evaluacion['summary'],
            'category': 'evaluaciones',
        }
    ]
    if action_juego['title']:
        classic_recommendations.insert(1, {
            'title': f"🎮 Juego: {action_juego['title']}",
            'summary': action_juego['summary'],
            'category': 'juegos',
        })

    # Guardar en base de datos para persistencia en ai_recommendations
    try:
        for cr in classic_recommendations:
            db_service.insert_recommendation(student_id, cr['title'], cr['summary'])
    except Exception:
        pass

    return {
        'success': True,
        'student_diagnosis': diagnosis,
        'primary_topic': weak_topic_name,
        'headline': f"Te recomendamos este plan personalizado para {weak_topic_name}:",
        'actions': actions,
        'recommendations': classic_recommendations,
    }
