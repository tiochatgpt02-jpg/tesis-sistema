from datetime import datetime
from services.ai_service import generate_student_learning_pack, generate_topic_content
from services.teacher_service import build_evaluation_questions, build_topic_generation_payload
from services import db_service
from services.ml_service import predict_student_performance


def build_topic_lesson(topic, grade, student_name='Estudiante', performance=0):
    payload = build_topic_generation_payload(topic.get('title', 'Tema'), grade)
    generated = generate_topic_content(topic.get('title', 'Tema'), grade)
    raw_description = generated.get('description') or payload.get('description') or ''
    clean_description = raw_description.replace('**', '').replace('##', '').replace('#', '').replace('\n', ' ')
    clean_description = ' '.join(clean_description.split())
    payload['description'] = clean_description[:500]
    payload['topic_id'] = topic.get('id')
    payload['title'] = topic.get('title', payload['title'])
    personalized = generate_student_learning_pack(topic.get('title', 'Tema'), grade, student_name, performance)
    payload['activities'] = personalized['activities']
    payload['evaluation_questions'] = personalized['evaluation']
    payload['game'] = personalized['game']
    payload['ai_source'] = personalized.get('source', 'local')
    payload['ai_notice'] = personalized.get('aviso')
    assigned = db_service.fetch_topic_learning_items(topic.get('id'))
    if assigned.get('activities'):
        payload['activities'] = assigned['activities']
    if assigned.get('games'):
        payload['game'] = assigned['games'][0]
    if assigned.get('evaluations'):
        payload['evaluation_questions'] = assigned['evaluations'][0].get('questions', payload['evaluation_questions'])
    return payload


def grade_activity(student_id, topic_id, answers, started_at=None, activity_type='actividades'):
    payload = build_topic_generation_payload('Actividad', 5)
    assigned = db_service.fetch_topic_learning_items(topic_id)
    topic = db_service.fetch_topic_by_id(topic_id) or {}
    topic_title = topic.get('title', 'Tema')
    student = db_service.fetch_student_by_id(student_id) or {}
    progress = db_service.fetch_student_progress(student_id)
    personalized = generate_student_learning_pack(
        topic_title,
        student.get('grade', 5),
        student.get('first_name', 'Estudiante'),
        progress.get('average_grade', 0),
    )
    base_activities = personalized.get('activities') or assigned.get('activities') or payload['activities']
    evaluation_questions = personalized.get('evaluation') or _questions_for_topic(topic)[0]
    activities = base_activities if activity_type != 'evaluaciones' else [
        {
            'question': item['question'],
            'correct_answer': item.get('answer', item.get('correct_answer', '')),
            'score': item.get('score', 10),
        }
        for item in evaluation_questions
    ]
    correct = 0
    results = []
    answers = answers or {}

    for index, activity in enumerate(activities):
        expected = str(activity.get('correct_answer', '')).strip().lower()
        received = str(answers.get(str(index), '')).strip().lower()
        
        # Coincidencia flexible para evaluación de alumno
        is_correct = bool(received) and bool(expected) and received == expected
        if is_correct:
            correct += 1

        results.append({
            'index': index,
            'question': activity['question'],
            'correct': is_correct,
            'expected': activity.get('correct_answer', ''),
            'answer': answers.get(str(index), ''),
        })

    total = len(activities)
    score_20 = round((correct / total) * 20, 2) if total else 0.0
    percentage_100 = round((correct / total) * 100, 2) if total else 0.0
    elapsed_seconds = 0
    if started_at:
        try:
            elapsed_seconds = max(0, int((datetime.utcnow() - datetime.fromisoformat(started_at)).total_seconds()))
        except (TypeError, ValueError):
            elapsed_seconds = 0

    time_limit_exceeded = activity_type == 'evaluaciones' and elapsed_seconds >= 20 * 60

    # Registrar el resultado en la base de datos con escalas normalizadas
    db_service.record_student_result(
        student_id=student_id,
        topic_id=topic_id,
        activity_type=activity_type,
        item_type='evaluation' if activity_type == 'evaluaciones' else 'lesson_activity',
        score=score_20,
        percentage=percentage_100,
        correct_answers=correct,
        wrong_answers=total - correct,
        time_spent_seconds=elapsed_seconds,
    )

    # Retroalimentación pedagógica formativa inmediata
    pedagogical_feedback = predict_student_performance(percentage_100, activity_type)
    score_label = f"Calificación: {score_20}/20 ({percentage_100}%)"
    ai_feedback = f"{score_label}. {correct} de {total} respuestas correctas. {pedagogical_feedback['advice']}"

    # Insertar recomendación personalizada si el desempeño necesita refuerzo o destaca
    db_service.insert_recommendation(
        student_id=student_id,
        title=f"Retroalimentación ({activity_type.capitalize()}): {pedagogical_feedback['level'].capitalize()}",
        summary=ai_feedback,
        topic_id=topic_id
    )

    return {
        'score': score_20,
        'percentage': percentage_100,
        'correct_answers': correct,
        'wrong_answers': total - correct,
        'results': results,
        'level': pedagogical_feedback['level'],
        'feedback': ai_feedback,
        'time_limit_exceeded': time_limit_exceeded,
    }


def _questions_for_topic(topic):
    title = topic.get('title', 'Tema')
    assigned = db_service.fetch_topic_learning_items(topic.get('id'))
    from services.ai_service import _fallback_quiz_questions, _normalize_quiz_questions

    best_questions = []
    for evaluation in assigned.get('evaluations') or []:
        parsed = _normalize_quiz_questions(title, evaluation.get('questions'))
        if len(parsed) > len(best_questions):
            best_questions = parsed
    if best_questions:
        return best_questions, 'ollama'

    activity_questions = []
    for activity in assigned.get('activities') or []:
        options = activity.get('options') or []
        if not isinstance(options, list) or len(options) < 2:
            continue
        activity_questions.append({
            'id': activity.get('id'),
            'question': activity.get('question'),
            'options': options,
            'answer': activity.get('correct_answer') or activity.get('answer') or '',
            'score': activity.get('score', 2),
        })
    activity_questions = _normalize_quiz_questions(title, activity_questions)
    if activity_questions:
        return activity_questions, 'actividades'

    return _fallback_quiz_questions(title), 'local'


def build_evaluation(topic, grade, student_name='Estudiante', performance=0):
    questions, source = _questions_for_topic(topic)
    personalized = generate_student_learning_pack(topic.get('title', 'Tema'), grade, student_name, performance)
    questions = personalized['evaluation']
    source = personalized.get('source', source)
    return {
        'topic_id': topic.get('id'),
        'title': f"Evaluación: {topic.get('title', 'Tema')}",
        'difficulty': 'media',
        'duration_minutes': 20,
        'questions': questions,
        'source': source,
    }


def build_student_progress(student_id, topics):
    from services.grading_policy_service import academic_average, get_policy
    policy = get_policy()
    academic_grade = academic_average(db_service.fetch_student_results(student_id=student_id), policy)
    progress = db_service.fetch_student_progress(student_id)
    activity_summary = db_service.fetch_student_activity_summary(student_id)
    topic_ids = {int(topic.get('id')) for topic in topics or [] if topic.get('id') is not None}
    topic_progress = [item for item in db_service.fetch_topic_progress(student_id) if int(item.get('id', 0)) in topic_ids]
    completed_topics = sum(1 for item in topic_progress if item.get('completed'))
    overall = round(
        sum(float(item.get('score', 0) or 0) for item in topic_progress) / len(topic_progress),
        2,
    ) if topic_progress else int(progress.get('overall_progress', 0) or 0)
    return {
        'overall': overall,
        'completed': completed_topics,
        'average_grade': academic_grade,
        'average_status': 'pending' if academic_grade is None else ('weighted' if policy else 'provisional'),
        'study_time': progress.get('study_time', '0h'),
        'activities': activity_summary.get('activities', 0),
        'evaluations': activity_summary.get('evaluations', 0),
        'games': activity_summary.get('games', 0),
        'best_score': activity_summary.get('best_score', 0),
        'topics': topic_progress,
    }


def build_recommendations(student_id, progress=None, topics=None):
    """
    GOAL 6: Genera recomendaciones adaptativas personalizadas con IA + ML
    unificando notas, evaluaciones, juegos y predicción de riesgo.
    """
    try:
        from services.adaptive_recommendations_service import build_adaptive_recommendations
        adaptive_data = build_adaptive_recommendations(student_id)
        recs = adaptive_data.get('recommendations')
        if recs:
            return recs
    except Exception:
        pass

    # Fallback pedagógico si no estuviese disponible el motor
    return [
        {
            'title': "📖 Leer material: Fracciones básicas",
            'summary': "Repasa los conceptos clave para afianzar tu comprensión.",
            'category': 'material',
        },
        {
            'title': "🎮 Juego: Comparar fracciones",
            'summary': "Practica dinámicas interactivas para reforzar tus competencias.",
            'category': 'juegos',
        },
        {
            'title': "📝 Evaluación: Práctica corta",
            'summary': "Comprueba tu aprendizaje resolviendo una evaluación formativa breve.",
            'category': 'evaluaciones',
        }
    ]


def get_student_risk_feedback(risk_level, probability=None):
    """
    Retorna estado académico, mensaje motivacional y recomendaciones formativas
    según el nivel de riesgo predicho por el modelo ML.
    """
    normalized = str(risk_level or '').upper().strip()
    if normalized in ('HIGH', 'ALTO'):
        return {
            'risk_level': 'HIGH',
            'risk_level_label': 'Alto',
            'academic_status': '⚠ Necesitas reforzar algunos temas',
            'motivational_message': '💪 No te rindas. Todavía puedes mejorar. Practica un poco cada día.',
            'badge_class': 'bg-danger',
            'recommendations': [
                'Practica los temas de sesiones anteriores',
                'Revisa el material disponible en tu aula virtual',
                'Realiza actividades de refuerzo y retos',
            ],
        }
    elif normalized in ('MEDIUM', 'MEDIO'):
        return {
            'risk_level': 'MEDIUM',
            'risk_level_label': 'Medio',
            'academic_status': '🚀 Vas avanzando, continúa practicando',
            'motivational_message': '🚀 Vas avanzando. Continúa practicando para mejorar.',
            'badge_class': 'bg-warning text-dark',
            'recommendations': [
                'Continúa practicando los retos de cada sesión',
                'Revisa el material disponible para afianzar conceptos',
                'Realiza actividades de refuerzo antes de tus evaluaciones',
            ],
        }
    elif normalized in ('LOW', 'BAJO'):
        return {
            'risk_level': 'LOW',
            'risk_level_label': 'Bajo',
            'academic_status': '⭐ Excelente desempeño académico',
            'motivational_message': '⭐ Excelente trabajo. Sigue manteniendo tu esfuerzo.',
            'badge_class': 'bg-success',
            'recommendations': [
                'Sigue manteniendo tu esfuerzo constante',
                'Explora desafíos y juegos educativos adicionales',
                'Revisa los nuevos temas para seguir aprendiendo',
            ],
        }
    else:
        return {
            'risk_level': 'UNKNOWN',
            'risk_level_label': 'No disponible',
            'academic_status': 'ℹ Información en proceso de recopilación',
            'motivational_message': '¡Continúa con tus clases y actividades! Tu esfuerzo diario es lo más importante.',
            'badge_class': 'bg-secondary',
            'recommendations': [
                'Revisa el material disponible de tus temas',
                'Realiza tus actividades formativas para medir tu avance',
            ],
        }


def build_student_risk_payload(student_id):
    """
    Consulta el servicio de predicción ML para el estudiante autenticado y empaqueta
    la respuesta con factores explicativos, mensaje motivacional y recomendaciones.
    """
    from services.ml.prediction_service import get_risk_prediction_service

    svc = get_risk_prediction_service()
    if not svc.is_available():
        meta = svc.get_status() if hasattr(svc, 'get_status') else {}
        feedback = get_student_risk_feedback('UNKNOWN')
        return {
            'success': False,
            'code': 'MODEL_NOT_AVAILABLE',
            'message': meta.get('message') or 'El modelo predictivo de riesgo académico no está disponible en este momento. Se requiere entrenamiento previo.',
            'student_id': int(student_id),
            'risk_level': 'UNKNOWN',
            'risk_level_label': 'No disponible',
            'probability': None,
            'factors': ['Modelo predictivo no disponible aún en el sistema'],
            'academic_status': 'ℹ Modelo predictivo no disponible',
            'motivational_message': feedback['motivational_message'],
            'recommendations': feedback['recommendations'],
            'badge_class': 'bg-secondary',
        }

    try:
        pred = svc.predict_for_student(int(student_id))
    except Exception as exc:
        feedback = get_student_risk_feedback('UNKNOWN')
        return {
            'success': False,
            'code': 'PREDICTION_ERROR',
            'message': f'Error al calcular predicción de riesgo: {str(exc)}',
            'student_id': int(student_id),
            'risk_level': 'UNKNOWN',
            'risk_level_label': 'No disponible',
            'probability': None,
            'factors': ['Error al procesar historial del estudiante'],
            'academic_status': 'ℹ Información temporalmente no disponible',
            'motivational_message': feedback['motivational_message'],
            'recommendations': feedback['recommendations'],
            'badge_class': 'bg-secondary',
        }

    if not pred.get('success'):
        code = pred.get('code', 'MODEL_NOT_AVAILABLE')
        msg = pred.get('message', 'Predicción no disponible.')
        feedback = get_student_risk_feedback('UNKNOWN')
        return {
            'success': False,
            'code': code,
            'message': msg,
            'student_id': int(student_id),
            'risk_level': 'UNKNOWN',
            'risk_level_label': 'No disponible',
            'probability': None,
            'factors': pred.get('main_factors') or ['Predicción no disponible'],
            'academic_status': 'ℹ Información temporalmente no disponible',
            'motivational_message': feedback['motivational_message'],
            'recommendations': feedback['recommendations'],
            'badge_class': 'bg-secondary',
        }

    pred_data = pred.get('prediction', {})
    raw_level = pred_data.get('risk_level') or pred.get('risk_level') or 'LOW'
    raw_prob = pred_data.get('probability')
    if raw_prob is None:
        raw_prob = pred.get('risk_probability')

    prob = round(float(raw_prob), 2) if raw_prob is not None else None
    factors = pred.get('main_factors') or pred.get('factors') or []
    if not factors:
        factors = ['Desempeño general registrado en el aula virtual']

    feedback = get_student_risk_feedback(raw_level, prob)

    return {
        'success': True,
        'student_id': int(student_id),
        'risk_level': feedback['risk_level'],
        'risk_level_label': feedback['risk_level_label'],
        'probability': prob,
        'academic_status': feedback['academic_status'],
        'motivational_message': feedback['motivational_message'],
        'factors': factors,
        'recommendations': feedback['recommendations'],
        'badge_class': feedback['badge_class'],
    }
