import json
import os
import re
import time

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from werkzeug.utils import secure_filename
from services.presentation_storage import (
    delete_stored_presentation_file,
    save_presentation_file,
    send_presentation_file,
)

from config import Config
from services.academic_calendar_service import school_today
from services.literal_history_service import fetch_history
from services.ai_service import check_ollama_status, generate_topic_content, generate_topic_learning_pack, generate_questions_from_teacher_material
from services.ml_service import build_prediction_payload
from services.ml.prediction_service import get_risk_prediction_service
from services.db_service import (
    fetch_all_topics,
    fetch_students,
    fetch_registered_students_for_messages,
    ensure_student_records_for_registered_users,
    insert_student,
    delete_student,
    update_student_observations,
    insert_topic,
    update_topic,
    delete_topic,
    fetch_messages_for_student,
    fetch_read_messages_for_teacher,
    delete_teacher_message,
    fetch_submissions,
    review_student_submission,
    record_student_result,
    send_message_to_student,
    fetch_alerts_for_user,
    get_unread_alerts_count,
    mark_alert_as_read,
    insert_presentation,
    get_presentations_for_topic,
    delete_presentation,
    fetch_presentation_by_id,
    fetch_presentation_by_topic_session,
    update_presentation,
    fetch_assessments_for_topic,
    update_assessment_status,
    fetch_materials_for_teacher,
    create_learning_material,
    delete_learning_material,
    fetch_material_by_id,
    update_learning_material_status,
    update_presentation_status,
    fetch_topic_learning_items,
    create_topic_activity,
    create_topic_game,
    create_topic_evaluation,
    clear_topic_learning_items,
    delete_topic_learning_item,
)
from services.teacher_reports_service import build_report_summary, build_student_risk_analysis
from services.teacher_service import build_evaluation_questions, build_teacher_dashboard_summary, build_topic_generation_payload

teacher_blueprint = Blueprint('teacher', __name__, url_prefix='/teacher')


def _save_generated_topic_content(topic_id, topic):
    clear_topic_learning_items(topic_id)
    title = topic.get('title', 'Tema')
    grade = int(topic.get('grade') or 5)
    pack = generate_topic_learning_pack(title, grade)
    questions = pack.get('preguntas') or build_evaluation_questions(title, grade)
    activity_ids = []
    for index, question in enumerate(questions[:4], start=1):
        activity_ids.append(create_topic_activity(
            topic_id,
            f"Actividad {index} de {title}",
            'selección múltiple',
            question.get('question', ''),
            question.get('options', []),
            question.get('answer', ''),
            int(question.get('score', 5)),
        ))
    juego = pack.get('juego') or {}
    game_id = create_topic_game(
        topic_id,
        juego.get('titulo', f"Juego de {title}"),
        juego.get('instrucciones', ''),
        json.dumps(juego.get('pares') or [], ensure_ascii=False),
    )
    evaluation_id = create_topic_evaluation(topic_id, 'media', questions)
    return activity_ids, game_id, evaluation_id, questions


def _auth_check():
    if 'user' not in session or not session.get('is_authenticated'):
        return redirect(url_for('auth.login'))
    if session.get('user_role') != 'teacher':
        return redirect(url_for('student.student_home'))
    return None


@teacher_blueprint.route('/')
def teacher_home():
    denied = _auth_check()
    if denied:
        return denied

    ensure_student_records_for_registered_users()
    students = fetch_students()
    message_students = fetch_registered_students_for_messages()
    topics = fetch_all_topics()
    summary = build_teacher_dashboard_summary(
        students=students,
        topics=topics,
        activities_count=18,
        evaluations_count=11,
    )
    ollama = check_ollama_status()
    teacher_name = session.get('teacher_name', 'Profesor')
    academic_year = school_today().year
    institutional_notes = {period: {} for period in range(1, 5)}
    for record in fetch_history(year=academic_year):
        if record.get('subject', 'computacion') != 'computacion':
            continue
        period = int(record['period'])
        rating = record['final_rating']
        if period not in institutional_notes or rating not in ('AD', 'A', 'B', 'C'):
            continue
        unit = re.match(r'Unidad ([1-8]) - ', record.get('source_name') or '')
        label = f'{rating} · Unidad {unit[1]}' if unit else rating
        institutional_notes[period][int(record['student_id'])] = label
    notes_period = max((period for period, notes in institutional_notes.items() if notes), default=1)

    return render_template(
        'teacher_dashboard.html',
        students=students,
        message_students=message_students,
        topics=topics,
        summary=summary,
        teacher_name=teacher_name,
        alerts_count=len(summary.get('alerts', [])),
        ollama=ollama,
        academic_year=academic_year,
        institutional_notes=institutional_notes,
        notes_period=notes_period,
    )


@teacher_blueprint.route('/students')
def manage_students():
    denied = _auth_check()
    if denied:
        return denied

    students = fetch_students()
    return render_template('teacher_students.html', students=students)


@teacher_blueprint.route('/topics')
def teacher_topics():
    denied = _auth_check()
    if denied:
        return denied

    topics = fetch_all_topics()
    return render_template('teacher_topics.html', topics=topics)


@teacher_blueprint.route('/reports')
def teacher_reports():
    denied = _auth_check()
    if denied:
        return denied

    students = fetch_students()
    topics = fetch_all_topics()
    report_summary = build_report_summary(students, topics)
    student_risks = [
        build_student_risk_analysis(student)
        for student in students[:5]
    ]
    return render_template(
        'teacher_reports.html',
        students=students,
        topics=topics,
        report_summary=report_summary,
        student_risks=student_risks,
    )


@teacher_blueprint.route('/api/generate-topic', methods=['POST'])
def api_generate_topic():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    topic = (data.get('topic') or '').strip()
    grade = int(data.get('grade') or 5)
    if not topic:
        return jsonify({'error': 'Debes indicar un tema'}), 400

    payload = build_topic_generation_payload(topic, grade)
    content = generate_topic_content(topic, grade)
    payload['description'] = content.get('description', payload['description'])
    payload['title'] = content.get('title', payload['title'])
    payload['status'] = 'Completado'

    inserted_id = insert_topic(payload['title'], payload['description'], grade, 'Completado')
    if inserted_id:
        payload['id'] = inserted_id
        activity_ids, game_id, evaluation_id, questions = _save_generated_topic_content(inserted_id, payload)
        payload['generated_content'] = {
            'activities': len(activity_ids),
            'game': bool(game_id),
            'evaluation': bool(evaluation_id),
            'questions': questions,
        }
        payload['preguntas'] = questions

    return jsonify(payload)


@teacher_blueprint.route('/api/generate-preview', methods=['POST'])
def api_generate_preview():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    topic = (data.get('topic') or '').strip()
    grade = int(data.get('grade') or 5)
    if not topic:
        return jsonify({'error': 'Debes indicar un tema'}), 400

    pack = generate_topic_learning_pack(topic, grade)
    payload = build_topic_generation_payload(topic, grade)
    return jsonify({
        'title': payload['title'],
        'description': payload['description'],
        'grade': payload['grade'],
        'explanation': payload['explanation'],
        'examples': payload['examples'],
        'activities': payload['activities'],
        'game': pack.get('juego') or payload['game'],
        'preguntas': pack.get('preguntas') or [],
        'source': pack.get('source'),
    })


@teacher_blueprint.route('/ml-status', methods=['GET'])
def teacher_ml_status():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return redirect(url_for('auth.login'))

    svc = get_risk_prediction_service()
    status_data = svc.get_status()
    is_available = svc.is_available()

    results = {}
    try:
        results_file = svc.registry.base_dir / 'training_results.json'
        if results_file.exists():
            with results_file.open('r', encoding='utf-8') as f:
                results = json.load(f)
    except Exception:
        results = {}

    models = results.get('models', [])
    winner_name = status_data.get('name') or status_data.get('selected_algorithm') or 'No disponible'
    measured = status_data.get('test_metrics') or {}
    winner_metrics = {
        'accuracy': measured.get('accuracy'), 'recall': measured.get('positive_class_recall'),
        'f1': measured.get('positive_class_f1'), 'roc_auc': measured.get('roc_auc'),
    }
    import math
    winner_metrics = {key:value if isinstance(value,(int,float)) and math.isfinite(value) and 0<=value<=1 else None
                      for key,value in winner_metrics.items()}

    return render_template(
        'ml_status.html',
        status=status_data,
        is_available=is_available,
        winner_name=winner_name,
        winner_metrics=winner_metrics,
        models=models,
        source=svc.registry.source,
        comparison_scope=results.get('metric_scope'),
    )


@teacher_blueprint.route('/api/predict-student', methods=['POST'])
def api_predict_student():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    student_id = data.get('student_id')
    cutoff_date = data.get('cutoff_date')
    student_name = (data.get('student_name') or '').strip() or 'Estudiante'
    activity_type = (data.get('activity_type') or 'actividades').strip() or 'actividades'
    raw_score = data.get('score')
    try:
        score = float(raw_score) if raw_score is not None else 0.0
    except (TypeError, ValueError):
        score = 0.0

    payload = build_prediction_payload(
        student_name=student_name,
        score=score,
        activity_type=activity_type,
        student_id=student_id,
        cutoff_date=cutoff_date,
    )
    return jsonify(payload)


@teacher_blueprint.route('/api/students/<int:student_id>/risk', methods=['GET'])
def api_student_risk(student_id: int):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    cutoff_date = request.args.get('cutoff_date')
    svc = get_risk_prediction_service()
    res = svc.predict_for_student(student_id=student_id, cutoff_date=cutoff_date)

    student_name = f"Estudiante {student_id}"
    try:
        students = fetch_students() or []
        for s in students:
            if s.get('id') == student_id or s.get('student_id') == student_id:
                student_name = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or student_name
                break
    except Exception:
        pass

    if not res.get('success'):
        return jsonify({
            'student_id': student_id,
            'student_name': student_name,
            'success': False,
            'code': res.get('code', 'MODEL_NOT_AVAILABLE'),
            'message': res.get('message', 'Modelo no disponible'),
            'prediction': {'risk_level': 'UNKNOWN', 'probability': None},
            'model': res.get('model', {'name': 'None', 'version': None, 'dataset': svc.registry.source}),
            'explanation': res.get('explanation', []),
            'main_factors': res.get('main_factors', []),
        })

    model_info = res.get('model', {})
    return jsonify({
        'student_id': student_id,
        'student_name': student_name,
        'success': True,
        'risk_probability': res.get('risk_probability'),
        'validation_scope': res.get('validation_scope'),
        'notice': res.get('notice'),
        'prediction': {
            'risk_level': res.get('prediction', {}).get('risk_level', 'UNKNOWN'),
            'probability': res.get('risk_probability'),
        },
        'model': {
            'name': model_info.get('name', 'SupervisedModel'),
            'version': model_info.get('version', '1.0'),
            'dataset': model_info.get('dataset', 'benchmark'),
        },
        'explanation': res.get('explanation', []),
        'main_factors': res.get('main_factors', []),
        'risk_level': res.get('risk_level'),
    })


@teacher_blueprint.route('/api/students', methods=['POST'])
def api_create_student():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    grade = data.get('grade')

    if not first_name or not last_name or not grade:
        return jsonify({'error': 'Nombre, apellido y grado son requeridos'}), 400

    try:
        student = insert_student(first_name, last_name, int(grade))
        return jsonify({'success': True, 'student': student}), 201
    except Exception as exc:
        return jsonify({'error': f'Error al crear estudiante: {str(exc)}'}), 500


@teacher_blueprint.route('/api/students/<int:student_id>', methods=['DELETE'])
def api_delete_student(student_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        delete_student(student_id)
        return jsonify({'success': True, 'deleted': student_id}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al eliminar estudiante: {str(exc)}'}), 500


@teacher_blueprint.route('/api/students/<int:student_id>/observations', methods=['PUT'])
def api_update_student_observations(student_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    observations = (data.get('observations') or '').strip()

    try:
        update_student_observations(student_id, observations)
        return jsonify({'success': True, 'student_id': student_id, 'observations': observations}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al guardar observaciones: {str(exc)}'}), 500


@teacher_blueprint.route('/api/messages/<int:student_id>', methods=['GET'])
def api_get_student_messages(student_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        messages = fetch_messages_for_student(student_id)
        return jsonify({'success': True, 'messages': messages, 'total': len(messages)}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al obtener mensajes: {str(exc)}'}), 500


@teacher_blueprint.route('/api/messages/<int:message_id>', methods=['DELETE'])
def api_delete_message(message_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        delete_teacher_message(message_id)
        return jsonify({'success': True, 'message': 'Mensaje eliminado correctamente'}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al eliminar mensaje: {str(exc)}'}), 500


@teacher_blueprint.route('/api/submissions', methods=['GET'])
def api_get_submissions():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify({'success': True, 'submissions': fetch_submissions()}), 200


@teacher_blueprint.route('/api/submissions/review', methods=['PUT'])
def api_review_submission_manual():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    student_id = data.get('student_id')
    if student_id is None:
        return jsonify({'error': 'Debe indicar el estudiante'}), 400

    try:
        score = float(data.get('score'))
    except (TypeError, ValueError):
        return jsonify({'error': 'La nota debe ser numérica'}), 400
    if not 0 <= score <= 20:
        return jsonify({'error': 'La nota debe estar entre 0 y 20'}), 400

    topic_raw = data.get('topic_id')
    topic_id = None if topic_raw in (None, '', 'null', 'None') else int(topic_raw)
    record_student_result(
        int(student_id),
        topic_id,
        'actividades',
        'entrega_revisada',
        score,
        correct_answers=0,
        wrong_answers=0,
        time_spent_seconds=0,
        percentage=score * 5,
    )
    return jsonify({'success': True, 'student_id': int(student_id), 'topic_id': topic_id}), 200


@teacher_blueprint.route('/api/submissions/<int:submission_id>/review', methods=['PUT'])
def api_review_submission(submission_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.get_json() or {}
    try:
        score = float(data.get('score'))
    except (TypeError, ValueError):
        return jsonify({'error': 'La nota debe ser numérica'}), 400
    if not 0 <= score <= 20:
        return jsonify({'error': 'La nota debe estar entre 0 y 20'}), 400

    submission = None
    for item in fetch_submissions() or []:
        if int(item.get('id')) == int(submission_id):
            submission = item
            break

    if not submission:
        return jsonify({'error': 'Entrega no encontrada'}), 404

    review_student_submission(submission_id, score, (data.get('feedback') or '').strip())

    student_id = submission.get('student_id')
    topic_id = submission.get('topic_id')
    if student_id is not None and topic_id is not None:
        record_student_result(
            int(student_id),
            int(topic_id),
            'actividades',
            f'submission:{submission_id}',
            score,
            correct_answers=0,
            wrong_answers=0,
            time_spent_seconds=0,
            percentage=score * 5,
        )

    return jsonify({'success': True, 'student_id': student_id, 'topic_id': topic_id}), 200


@teacher_blueprint.route('/api/topic/<int:topic_id>/materials', methods=['GET', 'POST'])
def api_topic_materials(topic_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    if request.method == 'GET':
        return jsonify({'success': True, 'materials': fetch_materials_for_teacher(topic_id)})
    data = request.get_json(silent=True) or request.form or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    material_type = (data.get('material_type') or 'texto').strip()
    description = (data.get('description') or (content[:120] + '...' if len(content) > 120 else content)).strip()
    if not title:
        return jsonify({'error': 'El título del material es obligatorio'}), 400
    if not content and not data.get('resource_url'):
        return jsonify({'error': 'El contenido o recurso del material es obligatorio'}), 400
    if material_type not in {'texto', 'imagen', 'video', 'presentacion', 'documento'}:
        material_type = 'texto'

    material_id = create_learning_material(
        topic_id, title, material_type, description,
        content, data.get('resource_url', ''),
    )
    return jsonify({
        'success': True,
        'material_id': material_id,
        'title': title,
        'topic_id': topic_id,
        'status': 'DRAFT',
    }), 201


@teacher_blueprint.route('/api/materials/<int:material_id>', methods=['DELETE'])
def api_delete_material(material_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    delete_learning_material(material_id)
    return jsonify({'success': True})


@teacher_blueprint.route('/api/materials/<int:material_id>/publish', methods=['POST'])
def api_publish_material(material_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    material = fetch_material_by_id(material_id)
    if not material or material.get('source') == 'presentation':
        return jsonify({'error': 'Material no encontrado', 'success': False}), 404
    update_learning_material_status(material_id, 'PUBLISHED')
    return jsonify({'success': True, 'material_id': material_id, 'status': 'PUBLISHED'}), 200


@teacher_blueprint.route('/api/materials/<int:material_id>/generate-activities', methods=['POST'])
def api_generate_material_activities(material_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    from services.db_service import fetch_material_by_id, create_topic_activity, create_topic_evaluation
    from services.ai_service import generate_questions_from_teacher_material

    material = fetch_material_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material educativo no encontrado'}), 404

    text = material.get('content') or material.get('description') or ''
    title = material.get('title') or 'Material'
    topic_id = material.get('topic_id')

    if not text:
        return jsonify({'error': 'El material no contiene texto suficiente para generar actividades'}), 400

    ai_result = generate_questions_from_teacher_material(text, title)
    if not ai_result.get('success'):
        return jsonify({'error': ai_result.get('error', 'Error al generar actividades')}), 400

    from services.practice_service import save_practice
    save_practice(f'material:{material_id}', text, int(material.get('grade') or 5), ai_result)

    questions = ai_result.get('questions', [])
    activities = ai_result.get('activities', [])

    created_activities = []
    for act in activities:
        act_id = create_topic_activity(
            topic_id=topic_id,
            title=act.get('title', f'Actividad de {title}'),
            activity_type='actividades',
            question=act.get('question', ''),
            options=act.get('options', []),
            correct_answer=act.get('correct_answer', ''),
            score=5,
        )
        created_activities.append(act_id)

    eval_id = None
    if questions:
        eval_id = create_topic_evaluation(
            topic_id=topic_id,
            difficulty='media',
            questions=questions,
        )

    return jsonify({
        'success': True,
        'material_id': material_id,
        'topic_id': topic_id,
        'questions': questions,
        'activities': activities,
        'created_activity_ids': created_activities,
        'created_evaluation_id': eval_id,
        'source': ai_result.get('source'),
    }), 201



@teacher_blueprint.route('/api/topic/<int:topic_id>/learning-items', methods=['GET', 'POST'])
def api_topic_learning_items(topic_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    if request.method == 'GET':
        return jsonify({'success': True, 'items': fetch_topic_learning_items(topic_id)})

    data = request.get_json() or {}
    item_type = data.get('item_type')
    if item_type == 'activity':
        required = ('title', 'activity_type', 'question', 'correct_answer')
        if any(not str(data.get(key, '')).strip() for key in required):
            return jsonify({'error': 'Faltan datos de la actividad'}), 400
        item_id = create_topic_activity(topic_id, data['title'], data['activity_type'], data['question'], data.get('options', []), data['correct_answer'], int(data.get('score', 5)))
    elif item_type == 'game':
        if not str(data.get('name', '')).strip():
            return jsonify({'error': 'El nombre del juego es requerido'}), 400
        item_id = create_topic_game(topic_id, data['name'], data.get('description', ''), data.get('rules', ''))
    elif item_type == 'evaluation':
        questions = data.get('questions') or []
        if not questions:
            return jsonify({'error': 'La evaluación debe tener preguntas'}), 400
        item_id = create_topic_evaluation(
            topic_id,
            data.get('difficulty', 'media'),
            build_evaluation_questions('Tema', 5, questions),
        )
    else:
        return jsonify({'error': 'Tipo de contenido no válido'}), 400
    return jsonify({'success': True, 'item_id': item_id}), 201


@teacher_blueprint.route('/api/topic/<int:topic_id>/auto-content', methods=['POST'])
def api_generate_topic_content(topic_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    topic = next((item for item in fetch_all_topics() if int(item.get('id')) == topic_id), None)
    if not topic:
        return jsonify({'error': 'Tema no encontrado'}), 404

    activity_ids, game_id, evaluation_id, questions = _save_generated_topic_content(topic_id, topic)
    return jsonify({
        'success': True,
        'title': topic['title'],
        'activity_ids': activity_ids,
        'game_id': game_id,
        'evaluation_id': evaluation_id,
        'preguntas': questions,
        'items': fetch_topic_learning_items(topic_id),
    }), 201


def _ensure_session_topic_for_grade(grade, session_number, section=None):
    grade = int(grade or session.get('user_grade') or 5)
    session_number = int(session_number or 1)
    unit_number = ((session_number - 1) // 4) + 1
    section = str(section or '').strip().upper() or None
    title = f'Sesión {session_number}'
    for topic in fetch_all_topics() or []:
        topic_section = str(topic.get('section') or '').strip().upper() or None
        if (
            int(topic.get('grade') or 0) == grade
            and topic_section == section
            and (
                int(topic.get('session_number') or 0) == session_number
                or str(topic.get('title') or '').strip() == title
            )
        ):
            return int(topic.get('id'))

    topic_id = insert_topic(
        title,
        f'Contenido de la sesión {session_number} del grado {grade}.',
        grade,
        'Pendiente',
        section,
        unit_number,
        session_number,
    )
    return int(topic_id)


@teacher_blueprint.route('/api/upload-presentation', methods=['POST'])
def api_upload_presentation():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        grade = request.form.get('grade', type=int) or session.get('user_grade') or 5
        session_number = request.form.get('session_number', 1, type=int) or 1
        section = (request.form.get('section') or '').strip().upper() or None
        uploaded_file = request.files.get('file')
        allowed = {'ppt', 'pptx', 'pdf', 'doc', 'docx'}

        if not uploaded_file or not uploaded_file.filename:
            return jsonify({'error': 'Debes seleccionar un archivo PPT o PDF'}), 400
        extension = uploaded_file.filename.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.filename else ''
        if extension not in allowed:
            return jsonify({'error': 'Solo se permiten archivos PPT, PPTX, PDF, DOC o DOCX'}), 400
        if not 1 <= session_number <= 32:
            return jsonify({'error': 'La sesión debe estar entre 1 y 32'}), 400
        requested_topic_id = request.form.get('topic_id', type=int)
        if requested_topic_id is not None:
            topic = next(
                (item for item in fetch_all_topics() or [] if int(item.get('id')) == requested_topic_id),
                None,
            )
            if not topic:
                return jsonify({'error': 'El tema o sesión seleccionado ya no existe'}), 404
            topic_grade = int(topic.get('grade') or 0)
            topic_session = int(topic.get('session_number') or 0)
            if topic_grade != grade:
                return jsonify({'error': 'El grado del archivo no coincide con el tema seleccionado'}), 400
            if topic_session and topic_session != session_number:
                return jsonify({'error': 'La sesión del archivo no coincide con el tema seleccionado'}), 400
            topic_id = requested_topic_id
            section = str(topic.get('section') or '').strip().upper() or None
        else:
            topic_id = _ensure_session_topic_for_grade(grade, session_number, section)
        title = (request.form.get('title') or '').strip() or f"Presentación PPT - Sesión {session_number}"
        description = (request.form.get('description') or '').strip()
        publish_to_students = (request.form.get('publish_to_students') or '').strip().lower() in {'true', '1', 'on'}
        presentation_status = 'PUBLISHED' if publish_to_students else 'DRAFT'

        filename = f'{time.time_ns()}_{secure_filename(uploaded_file.filename)}'
        file_path, file_size = save_presentation_file(uploaded_file, filename)

        existing = fetch_presentation_by_topic_session(topic_id, session_number)
        replaced = existing is not None

        if existing:
            delete_stored_presentation_file(existing.get('file_path'))
            presentation_id = existing['id']
            update_presentation(presentation_id, title, description, file_path, filename, file_size, presentation_status)
        else:
            presentation_id = insert_presentation(
                topic_id, title, session_number, description, file_path,
                filename, file_size, session.get('user_id'), presentation_status,
            )

        invalidated_assessments = fetch_assessments_for_topic(topic_id, status='PUBLISHED')
        for assessment in invalidated_assessments:
            update_assessment_status(assessment['id'], 'PENDING_REVIEW')

        return jsonify({'success': True, 'presentation_id': presentation_id, 'topic_id': topic_id, 'file_path': f'/teacher/api/presentations/{presentation_id}/file', 'replaced': replaced, 'invalidated_assessments': len(invalidated_assessments), 'grade': grade, 'section': section, 'session_number': session_number, 'unit_number': ((session_number - 1) // 4) + 1, 'status': presentation_status}), 201
    except Exception as e:
        return jsonify({'error': f'Error al subir el archivo: {str(e)}'}), 500


@teacher_blueprint.route('/api/presentations/<int:topic_id>', methods=['GET'])
def api_topic_presentations(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify({'success': True, 'presentations': get_presentations_for_topic(topic_id)})


@teacher_blueprint.route('/api/presentations/<int:presentation_id>/publish', methods=['POST'])
def api_publish_presentation(presentation_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    presentation = fetch_presentation_by_id(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentación no encontrada', 'success': False}), 404
    update_presentation_status(presentation_id, 'PUBLISHED')
    return jsonify({
        'success': True,
        'presentation_id': presentation_id,
        'topic_id': presentation.get('topic_id'),
        'status': 'PUBLISHED',
    }), 200


@teacher_blueprint.route('/api/presentations/<int:presentation_id>/file', methods=['GET'])
def api_teacher_presentation_file(presentation_id):
    denied = _auth_check()
    if denied:
        return denied
    presentation = fetch_presentation_by_id(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentación no encontrada'}), 404
    try:
        return send_presentation_file(
            presentation.get('file_path'),
            presentation.get('file_name') or 'presentacion',
        )
    except FileNotFoundError:
        return jsonify({'error': 'No se encontró el archivo de la presentación'}), 404


@teacher_blueprint.route('/api/delete-presentation/<int:presentation_id>', methods=['DELETE'])
def api_delete_presentation(presentation_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    presentation = fetch_presentation_by_id(presentation_id)
    if presentation:
        delete_stored_presentation_file(presentation.get('file_path'))
    delete_presentation(presentation_id)
    return jsonify({'success': True})


@teacher_blueprint.route('/api/learning-items/<item_type>/<int:item_id>', methods=['DELETE'])
def api_delete_learning_item(item_type, item_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    if not delete_topic_learning_item(item_type, item_id):
        return jsonify({'error': 'Tipo de contenido no válido'}), 400
    return jsonify({'success': True})


@teacher_blueprint.route('/api/topic/<int:topic_id>', methods=['PUT', 'DELETE'])
def api_topic_manage(topic_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    if request.method == 'DELETE':
        delete_topic(topic_id)
        return jsonify({'success': True, 'deleted': topic_id})

    data = request.get_json() or {}
    updated = update_topic(
        topic_id,
        title=data.get('title'),
        description=data.get('description'),
        grade=data.get('grade'),
        status=data.get('status'),
        section=data.get('section'),
        unit_number=data.get('unit_number'),
        session_number=data.get('session_number'),
    )
    return jsonify({'success': True, 'topic': updated})


@teacher_blueprint.route('/api/send-message', methods=['POST'])
def api_send_message():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    student_id = data.get('student_id')
    message = (data.get('message') or '').strip()

    if not student_id or not message:
        return jsonify({'error': 'Estudiante y mensaje son requeridos'}), 400

    try:
        message_id = send_message_to_student(int(student_id), message)
        return jsonify({
            'success': True,
            'message': 'Mensaje enviado correctamente',
            'message_id': message_id,
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error al enviar mensaje: {str(e)}'}), 500


@teacher_blueprint.route('/api/read-messages', methods=['GET'])
def api_get_read_messages():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify({'success': True, 'alerts': fetch_read_messages_for_teacher()}), 200


@teacher_blueprint.route('/api/alerts', methods=['GET'])
def api_get_alerts():
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    user_id = session.get('user_id')
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    try:
        alerts = fetch_alerts_for_user(user_id=user_id, unread_only=unread_only)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total': len(alerts),
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error al obtener alertas: {str(e)}'}), 500


@teacher_blueprint.route('/api/alerts/<int:alert_id>/read', methods=['PUT'])
def api_mark_alert_read(alert_id):
    denied = _auth_check()
    if denied and not Config.USE_MOCK_DATA:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        mark_alert_as_read(alert_id)
        return jsonify({
            'success': True,
            'message': 'Alerta marcada como leída',
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500
