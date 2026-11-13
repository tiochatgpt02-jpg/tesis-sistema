"""
Servicio de Juegos Interactivos de Reforzamiento (GOAL 5)
Gestiona la lógica lúdica de los 3 juegos formativos, la evaluación de respuestas,
la detección de debilidades conceptuales y las recomendaciones personalizadas.
"""
from typing import Dict, Any, List, Optional
from services import db_service

_TOPIC_STOP_WORDS = {'a', 'al', 'de', 'del', 'el', 'en', 'la', 'las', 'lo', 'los', 'y'}


def get_all_reinforcement_games() -> List[Dict[str, Any]]:
    """
    Retorna los 3 juegos de reforzamiento iniciales con sus metadatos y temas curriculares.
    """
    return db_service.fetch_reinforcement_games_catalog()


def get_reinforcement_game(game_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene un juego de reforzamiento por ID.
    """
    return db_service.fetch_reinforcement_game_by_id(game_id)


def evaluate_game_submission(game: Dict[str, Any], student_answer: Any, time_spent: int = 0) -> Dict[str, Any]:
    """
    Evalúa la respuesta del alumno para el juego seleccionado y entrega retroalimentación pedagógica.
    """
    raw_answer = str(student_answer or '').strip()
    clean_answer = raw_answer.lower()
    correct_answer = str(game.get('correct_answer') or '').strip().lower()
    acceptable = [correct_answer] + [str(a).strip().lower() for a in game.get('acceptable_answers', [])]

    game_type = game.get('game_type', 'opcion_multiple')
    is_correct = False

    if game_type == 'opcion_multiple':
        # Juego 1: ¿Cuánto es 5x5? Opciones: 20, 25, 30
        is_correct = (clean_answer == correct_answer) or (raw_answer == str(game.get('correct_answer')))
    elif game_type == 'verdadero_falso':
        # Juego 2: La tierra gira alrededor del sol. Verdadero / Falso
        if clean_answer in ('verdadero', 'true', 'v', '1'):
            is_correct = (correct_answer in ('verdadero', 'true', 'v', '1'))
        elif clean_answer in ('falso', 'false', 'f', '0'):
            is_correct = (correct_answer in ('falso', 'false', 'f', '0'))
        else:
            is_correct = (clean_answer == correct_answer)
    elif game_type == 'completar':
        # Juego 3: La fotosíntesis ocurre en ______
        # Acepta "las hojas", "hojas", "los cloroplastos", etc.
        is_correct = any(clean_answer == acc or clean_answer in acc or acc in clean_answer for acc in acceptable)
    else:
        is_correct = (clean_answer in acceptable)

    # Puntajes
    score_vigesimal = 20.0 if is_correct else 8.0
    percentage = 100.0 if is_correct else 40.0
    feedback = game.get('feedback_correct') if is_correct else game.get('feedback_incorrect')

    return {
        'is_correct': is_correct,
        'student_answer': raw_answer,
        'expected_answer': game.get('correct_answer'),
        'score': score_vigesimal,
        'percentage': percentage,
        'feedback': feedback,
        'time_spent': int(time_spent),
    }


def detect_weaknesses_and_recommend_games(
    student_id: int,
    explicit_weak_topics: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Detecta debilidades académicas del alumno y recomienda el juego adecuado.
    Flujo:
    Alumno falla pregunta -> Sistema detecta debilidad -> Recomienda juego.
    """
    games = get_all_reinforcement_games()
    weak_tokens: List[str] = []

    # 1. Si se pasan temas débiles explícitos (ej. desde el examen de 15 preguntas)
    if explicit_weak_topics:
        for t in explicit_weak_topics:
            weak_tokens.extend(str(t).lower().split())

    # 2. Si no hay debilidades explícitas, consultar los últimos intentos fallidos del alumno
    if not weak_tokens:
        recent_attempts = db_service.fetch_student_assessment_attempts(student_id)
        for att in recent_attempts[:3]:
            reinforce = att.get('reinforce_topics') or []
            for t in reinforce:
                weak_tokens.extend(str(t).lower().split())

    # 3. Si aún no hay historial, revisar notas con baja calificación
    if not weak_tokens:
        notes = db_service.fetch_student_notes(student_id)
        low_notes = [n for n in notes if float(n.get('score', 20) or 20) < 11.0]
        for ln in low_notes:
            note_text = str(ln.get('notes', '')).lower()
            weak_tokens.extend(note_text.split())

    # 4. Mapear debilidades con palabras clave de cada juego
    recommended: List[Dict[str, Any]] = []
    seen_ids = set()

    clean_tokens = {
        tok.strip('.,;:!?¿¡()[]{}"\'')
        for tok in weak_tokens
        if tok.strip('.,;:!?¿¡()[]{}"\'') not in _TOPIC_STOP_WORDS
    }

    for game in games:
        gid = game['id']
        keywords = {
            token.strip('.,;:!?¿¡()[]{}"\'')
            for keyword in game.get('weakness_keywords', [])
            for token in str(keyword).lower().split()
            if token.strip('.,;:!?¿¡()[]{}"\'') not in _TOPIC_STOP_WORDS
        }
        topic_title_tokens = {
            token.strip('.,;:!?¿¡()[]{}"\'')
            for token in str(game.get('topic_title', '')).lower().split()
            if token.strip('.,;:!?¿¡()[]{}"\'') not in _TOPIC_STOP_WORDS
        }

        match_found = False
        matching_reason = ""

        for token in clean_tokens:
            if token in keywords or token in topic_title_tokens:
                match_found = True
                matching_reason = f"Detectamos oportunidad de mejora en: {game.get('topic_title')}"
                break

        if match_found and gid not in seen_ids:
            game_card = dict(game)
            game_card['recommendation_reason'] = matching_reason
            game_card['priority'] = 'ALTA'
            recommended.append(game_card)
            seen_ids.add(gid)

    return recommended
