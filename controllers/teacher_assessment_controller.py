from flask import Blueprint, jsonify, request, session
from config import Config
from services.ai_service import generate_questions_from_teacher_material
from services.material_extractor_service import MaterialExtractorService
from services.teacher_assessment_service import generate_assessment, grade_assessment
from services.db_service import (
    create_assessment,
    update_assessment_status,
    fetch_assessment_by_id,
    fetch_all_assessments,
    fetch_assessments_for_topic,
    create_question,
    update_question,
    delete_question,
    approve_question,
    fetch_topic_by_id,
    create_topic_evaluation,
    get_presentations_for_topic,
)

teacher_assessment_blueprint = Blueprint('teacher_assessment', __name__, url_prefix='/teacher')


def _teacher_check():
    if not session.get('is_authenticated') or 'user' not in session:
        if not Config.USE_MOCK_DATA:
            return jsonify({'error': 'No autorizado', 'success': False}), 401
    if session.get('user_role') and session.get('user_role') != 'teacher':
        return jsonify({'error': 'Requiere permisos de profesor', 'success': False}), 403
    return None


# =========================================================
# Endpoints Legados / Compatibilidad
# =========================================================

@teacher_assessment_blueprint.route('/api/assessment/generate', methods=['POST'])
def api_generate_assessment():
    payload = request.get_json() or {}
    assessment = generate_assessment(
        payload.get('topic', 'Tema'),
        payload.get('grade', 5),
        payload.get('question_count', 3),
        payload.get('difficulty', 'media'),
    )
    return jsonify(assessment)


@teacher_assessment_blueprint.route('/api/assessment/grade', methods=['POST'])
def api_grade_assessment():
    payload = request.get_json() or {}
    result = grade_assessment(payload.get('submissions', []))
    return jsonify(result)


# =========================================================
# GOAL 3 — Flujo de Aprobación Docente de Evaluaciones IA
# =========================================================

@teacher_assessment_blueprint.route('/api/assessments/generate', methods=['POST'])
def api_generate_ai_assessment():
    """
    La IA genera preguntas para el tema indicado, pero NUNCA se publican automáticamente.
    Estado inicial: GENERATED -> PENDING_REVIEW.
    Preguntas iniciales: approved = False.
    """
    denied = _teacher_check()
    if denied:
        return denied

    data = request.get_json(silent=True) or request.form or {}
    kind = data.get('kind', 'exam')
    if kind not in ('practice', 'exam'):
        return jsonify({'success': False, 'error': 'Selecciona práctica o examen.'}), 400
    topic_id = data.get('topic_id')
    if not topic_id:
        return jsonify({'error': 'Debes indicar el ID del tema (topic_id)', 'success': False}), 400

    topic = fetch_topic_by_id(topic_id) or {}
    topic_title = topic.get('title') or data.get('topic_title') or f"Tema {topic_id}"
    grade = int(topic.get('grade') or data.get('grade') or 5)
    title = (data.get('title') or f"Evaluación de {topic_title}").strip()
    try:
        question_count = int(data.get('question_count') or 15)
        if not 1 <= question_count <= 15:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'El número de preguntas debe estar entre 1 y 15.'}), 400

    presentations = get_presentations_for_topic(int(topic_id))
    if not presentations:
        return jsonify({
            'error': 'Este tema no tiene una presentación. Sube un PPT para poder crear la evaluación.',
            'success': False,
        }), 400

    presentation = max(
        presentations,
        key=lambda item: (int(item.get('session_number') or 0), int(item.get('id') or 0)),
    )
    try:
        extracted = MaterialExtractorService.extract_from_presentation_record(presentation)
    except (FileNotFoundError, ValueError, OSError) as exc:
        return jsonify({'error': str(exc), 'success': False}), 400

    raw_pack = generate_questions_from_teacher_material(
        extracted.get('raw_text'),
        extracted.get('title') or topic_title,
        grade=grade,
        num_questions=question_count,
        timeout=45,
    )
    raw_questions = [
        q for q in (raw_pack.get('questions') or [])
        if str(q.get('question') or '').strip() and len(q.get('options') or []) >= 2
    ]
    unique_questions = set()
    verified_questions = []
    for question in raw_questions:
        options = list(dict.fromkeys(str(value).strip() for value in question.get('options', []) if str(value).strip()))
        answer = str(question.get('answer') or '').strip()
        if len(options) < 2 or answer not in options:
            continue
        if answer not in options[:3]:
            options = options[:2] + [answer]
        question = {**question, 'options': options[:3], 'answer': answer}
        normalized_question = str(question.get('question') or '').strip().casefold()
        if normalized_question and normalized_question not in unique_questions:
            unique_questions.add(normalized_question)
            verified_questions.append(question)
    if not verified_questions:
        return jsonify({
            'error': raw_pack.get('error') or 'No se pudieron verificar preguntas a partir del contenido del PPT.',
            'success': False,
        }), 422
    raw_questions = verified_questions[:question_count]

    # 1. Crear Assessment en estado GENERATED
    teacher_id = session.get('user_id') or session.get('teacher_id') or 1
    assessment_id = create_assessment(
        topic_id=int(topic_id),
        title=title,
        teacher_id=int(teacher_id),
        status='GENERATED', kind=kind,
    )

    # 2. Transicionar a PENDING_REVIEW (disponible para revisión del docente)
    update_assessment_status(assessment_id, 'PENDING_REVIEW')

    # 3. Invocar IA para generar las preguntas
    saved_questions = []
    for q in raw_questions:
        q_text = str(q.get('question') or '').strip()
        options = q.get('options') or []
        answer = str(q.get('answer') or (options[0] if options else '')).strip()
        if answer not in [str(value).strip() for value in options]:
            continue
        # The legacy question table has three alternatives. Never drop the correct one.
        if answer not in [str(value).strip() for value in options[:3]]:
            options = list(options[:2]) + [answer]

        opt_a = str(options[0]).strip() if len(options) > 0 else 'Opción A'
        opt_b = str(options[1]).strip() if len(options) > 1 else 'Opción B'
        opt_c = str(options[2]).strip() if len(options) > 2 else 'Opción C'

        if not q_text:
            continue

        qid = create_question(
            assessment_id=assessment_id,
            question=q_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            answer=answer or opt_a,
            approved=False,  # REGLA: Nunca aprobada automáticamente
        )
        saved_questions.append({
            'id': qid,
            'assessment_id': assessment_id,
            'question': q_text,
            'option_a': opt_a,
            'option_b': opt_b,
            'option_c': opt_c,
            'answer': answer or opt_a,
            'approved': False,
        })

    return jsonify({
        'success': True,
        'assessment_id': assessment_id,
        'topic_id': int(topic_id),
        'title': title,
        'kind': kind,
        'presentation_id': presentation.get('id'),
        'presentation_title': presentation.get('title'),
        'source': raw_pack.get('source'),
        'status': 'PENDING_REVIEW',
        'questions': saved_questions,
        'message': (
            f'Evaluación creada con {len(saved_questions)} preguntas verificables del PPT. '
            'Requiere revisión docente antes de publicarse.'
        ),
    }), 201


@teacher_assessment_blueprint.route('/api/assessments', methods=['GET'])
def api_list_assessments():
    denied = _teacher_check()
    if denied:
        return denied

    status_filter = request.args.get('status')
    grade = request.args.get('grade', type=int)
    unit_number = request.args.get('unit', type=int)
    session_number = request.args.get('session_number', type=int)
    section = (request.args.get('section') or '').strip() or None
    if unit_number is not None and not 1 <= unit_number <= 8:
        return jsonify({'error': 'Unidad no válida', 'success': False}), 400
    if session_number is not None and not 1 <= session_number <= 32:
        return jsonify({'error': 'Sesión no válida', 'success': False}), 400
    assessments = fetch_all_assessments(
        status=status_filter,
        grade=grade,
        section=section,
        unit_number=unit_number,
        session_number=session_number,
    )
    return jsonify({
        'success': True,
        'assessments': assessments,
        'total': len(assessments),
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>', methods=['GET'])
def api_get_assessment(assessment_id):
    denied = _teacher_check()
    if denied:
        return denied

    assessment = fetch_assessment_by_id(assessment_id)
    if not assessment:
        return jsonify({'error': 'Evaluación no encontrada', 'success': False}), 404

    return jsonify({
        'success': True,
        'assessment': assessment,
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/questions/<int:question_id>', methods=['PUT'])
def api_update_assessment_question(assessment_id, question_id):
    denied = _teacher_check()
    if denied:
        return denied

    data = request.get_json(silent=True) or request.form or {}
    assessment = fetch_assessment_by_id(assessment_id)
    existing = next((question for question in (assessment or {}).get('questions', []) if int(question['id']) == question_id), None)
    if not existing:
        return jsonify({'success': False, 'error': 'La pregunta no pertenece a esta evaluación.'}), 404
    candidate_options = [str(data.get(key, existing.get(key)) or '').strip() for key in ('option_a', 'option_b', 'option_c')]
    candidate_answer = str(data.get('answer', existing.get('answer')) or '').strip()
    if not str(data.get('question', existing.get('question')) or '').strip() or len(set(candidate_options) - {''}) < 2 or candidate_answer not in candidate_options:
        return jsonify({'success': False, 'error': 'Completa la pregunta y las alternativas, e indica una respuesta que aparezca entre ellas.'}), 400
    question_text = data.get('question')
    option_a = data.get('option_a')
    option_b = data.get('option_b')
    option_c = data.get('option_c')
    answer = data.get('answer')
    approved = data.get('approved')

    success = update_question(
        question_id=question_id,
        question=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        answer=answer,
        approved=approved,
    )
    if not success:
        return jsonify({'error': 'No se pudo actualizar la pregunta', 'success': False}), 400
    update_assessment_status(assessment_id, 'PENDING_REVIEW')

    return jsonify({
        'success': True,
        'message': 'Pregunta actualizada correctamente por el docente',
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/questions/<int:question_id>', methods=['DELETE'])
def api_delete_assessment_question(assessment_id, question_id):
    denied = _teacher_check()
    if denied:
        return denied

    assessment = fetch_assessment_by_id(assessment_id)
    if not any(int(question['id']) == question_id for question in (assessment or {}).get('questions', [])):
        return jsonify({'success': False, 'error': 'La pregunta no pertenece a esta evaluación.'}), 404
    delete_question(question_id)
    update_assessment_status(assessment_id, 'PENDING_REVIEW')
    return jsonify({
        'success': True,
        'message': 'Pregunta eliminada de la evaluación',
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/questions', methods=['POST'])
def api_add_assessment_question(assessment_id):
    denied = _teacher_check()
    if denied:
        return denied

    data = request.get_json(silent=True) or request.form or {}
    question_text = (data.get('question') or '').strip()
    option_a = (data.get('option_a') or '').strip()
    option_b = (data.get('option_b') or '').strip()
    option_c = (data.get('option_c') or '').strip()
    answer = (data.get('answer') or option_a).strip()
    approved = bool(data.get('approved', False))

    if not question_text or not option_a or not option_b:
        return jsonify({'error': 'Enunciado y opciones mínimas son obligatorias', 'success': False}), 400

    qid = create_question(
        assessment_id=assessment_id,
        question=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c or 'Otra opción',
        answer=answer,
        approved=approved,
    )

    return jsonify({
        'success': True,
        'question_id': qid,
        'message': 'Pregunta agregada a la evaluación',
    }), 201


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/questions/<int:question_id>/approve', methods=['POST'])
def api_approve_single_question(assessment_id, question_id):
    denied = _teacher_check()
    if denied:
        return denied

    approve_question(question_id, True)
    return jsonify({
        'success': True,
        'message': 'Pregunta aprobada por el profesor',
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/approve', methods=['POST'])
def api_approve_assessment(assessment_id):
    """
    El profesor valida y aprueba la evaluación completa.
    Transiciona el estado de PENDING_REVIEW a APPROVED.
    """
    denied = _teacher_check()
    if denied:
        return denied

    assessment = fetch_assessment_by_id(assessment_id)
    if not assessment:
        return jsonify({'error': 'Evaluación no encontrada', 'success': False}), 404

    questions = assessment.get('questions', [])
    invalid_answers = [
        q for q in questions
        if str(q.get('answer') or '').strip() not in {
            str(q.get('option_a') or '').strip(),
            str(q.get('option_b') or '').strip(),
            str(q.get('option_c') or '').strip(),
        }
    ]
    if not questions or invalid_answers:
        return jsonify({
            'error': 'Agrega al menos una pregunta y verifica que cada respuesta correcta coincida con una de sus opciones antes de aprobar.',
            'success': False,
        }), 400

    # Si ninguna pregunta individual fue marcada, la aprobación general valida todas las preguntas.
    approved_count = sum(1 for q in questions if q.get('approved'))
    if approved_count == 0:
        for q in questions:
            approve_question(q['id'], True)

    update_assessment_status(assessment_id, 'APPROVED')

    return jsonify({
        'success': True,
        'status': 'APPROVED',
        'message': f'Evaluación aprobada con {len(questions)} preguntas. Puedes agregar más antes de publicarla.',
    }), 200


@teacher_assessment_blueprint.route('/api/assessments/<int:assessment_id>/publish', methods=['POST'])
def api_publish_assessment(assessment_id):
    """
    El profesor publica la evaluación aprobada.
    Transiciona de APPROVED (o PENDING_REVIEW) a PUBLISHED.
    A partir de este momento los alumnos podrán ver y rendir las preguntas aprobadas.
    """
    denied = _teacher_check()
    if denied:
        return denied

    assessment = fetch_assessment_by_id(assessment_id)
    if not assessment:
        return jsonify({'error': 'Evaluación no encontrada', 'success': False}), 404

    questions = assessment.get('questions', [])
    approved_questions = [q for q in questions if q.get('approved')]
    invalid_approved_answers = [
        q for q in approved_questions
        if str(q.get('answer') or '').strip() not in {
            str(q.get('option_a') or '').strip(),
            str(q.get('option_b') or '').strip(),
            str(q.get('option_c') or '').strip(),
        }
    ]
    if not approved_questions or invalid_approved_answers:
        return jsonify({
            'error': 'Aprueba al menos una pregunta y verifica que su respuesta correcta coincida con una de sus opciones antes de publicar.',
            'success': False,
        }), 400

    update_assessment_status(assessment_id, 'PUBLISHED')

    # Sincronizar hacia topic_evaluations para compatibilidad con vistas existentes
    topic_id = assessment.get('topic_id')
    approved_qs = [
        {
            'question': q['question'],
            'options': [q['option_a'], q['option_b'], q['option_c']],
            'answer': q['answer'],
            'score': 5,
        }
        for q in approved_questions
    ]
    if approved_qs and topic_id:
        create_topic_evaluation(topic_id, 'media', approved_qs)

    return jsonify({
        'success': True,
        'status': 'PUBLISHED',
        'message': '¡Evaluación publicada con éxito! Ya está disponible para los alumnos.',
    }), 200
