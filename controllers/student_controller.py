import os
from datetime import datetime, timezone

from flask import Blueprint, current_app, render_template, session, redirect, url_for, jsonify, request
from werkzeug.utils import secure_filename
import uuid
from services.learning_attempt_service import start_attempt, submit_attempt, public_attempt, AttemptError
from services.practice_service import get_practice
from services.presentation_storage import send_presentation_file
from services.db_service import (
    fetch_topics_for_grade,
    fetch_topic_by_id,
    fetch_student_by_id,
    fetch_student_progress,
    fetch_student_results,
    fetch_recommendations,
    get_presentations_for_topic,
    fetch_messages_for_student,
    get_unread_messages_count,
    mark_message_as_read,
    fetch_alerts_for_user,
    get_unread_alerts_count,
    mark_alert_as_read,
    fetch_learning_materials,
    mark_material_reviewed,
    fetch_material_by_id,
    fetch_presentation_by_id,
    fetch_all_materials_for_student,
    record_student_result,
    fetch_all_games_with_topics,
    create_student_submission,
    fetch_submissions,
    fetch_published_assessment_for_topic,
    fetch_assessments_for_topic,
    record_student_assessment_attempt,
    fetch_student_assessment_attempts,
    fetch_assessment_attempt_by_id,
    record_student_game_attempt,
    fetch_student_game_attempts,
    fetch_reinforcement_games_catalog,
    fetch_reinforcement_game_by_id,
    fetch_published_ai_games_for_topic,
    fetch_ai_generated_game_by_id,
    record_student_ai_game_attempt,
)
from services.game_engine import GameEngine
from services.reinforcement_games_service import (
    get_all_reinforcement_games,
    get_reinforcement_game,
    evaluate_game_submission,
    detect_weaknesses_and_recommend_games,
)
from services.student_learning_service import (
    build_evaluation,
    build_recommendations,
    build_student_progress,
    build_student_risk_payload,
    build_topic_lesson,
    get_student_risk_feedback,
    grade_activity,
)
from services.ai_service import generate_student_learning_pack, generate_questions_from_teacher_material
from services.material_extractor_service import MaterialExtractorService

student_blueprint = Blueprint('student', __name__, url_prefix='/student')


def _auth_check():
    if 'user' not in session or not session.get('is_authenticated'):
        return redirect(url_for('auth.login'))
    if session.get('user_role') != 'student':
        return redirect(url_for('teacher.teacher_home'))
    return None


def _current_student_section():
    student = fetch_student_by_id(session.get('student_id', 1)) or {}
    return str(student.get('section') or session.get('user_section') or '').strip().upper()


def _published_topic_for_student(topic_id):
    grade = session.get('user_grade') or 5
    topic = fetch_topic_by_id(topic_id)
    if not topic or int(topic.get('grade') or 0) != int(grade):
        return None
    topic_section = str(topic.get('section') or '').strip().upper()
    if topic_section and topic_section != _current_student_section():
        return None
    if str(topic.get('status') or '').strip() != 'Publicado':
        return None
    return topic


@student_blueprint.route('/')
def student_home():
    denied = _auth_check()
    if denied:
        return denied

    grade = session.get('user_grade') or 5
    student_id = session.get('student_id', 1)
    section = _current_student_section()
    topics = fetch_topics_for_grade(grade, section)
    progress_data = fetch_student_progress(student_id)

    last_topic = 'Sin temas aún'
    for t in topics:
        if t.get('status') == 'En proceso':
            last_topic = t['title']
            break
    if last_topic == 'Sin temas aún' and topics:
        last_topic = topics[0]['title']

    progress = {
        'overall': progress_data.get('overall_progress', 0),
        'completed': progress_data.get('completed_topics', 0),
        'study_time': progress_data.get('study_time', '0h'),
        'average_grade': progress_data.get('average_grade', 0),
    }
    progress = build_student_progress(student_id, topics)
    recommendations = build_recommendations(student_id, progress, topics)
    recent_results = fetch_student_results(student_id=student_id)[:4]
    recent_activities = []
    for result in recent_results:
        raw_score = float(result.get('score', 0) or 0)
        score = round(raw_score * 5) if result.get('activity_type') == 'evaluaciones' else round(raw_score)
        recent_activities.append({
            'title': result.get('topic') or 'Actividad de computación',
            'type': {'actividades': 'Actividad práctica', 'evaluaciones': 'Evaluación IA', 'juegos': 'Juego educativo'}.get(result.get('activity_type'), 'Actividad'),
            'score': score,
            'status': 'Completada' if score >= 60 else 'En progreso',
            'date': result.get('created_at', 'Hoy'),
        })

    student_name = session.get('student_name', session.get('user', 'Estudiante'))
    next_classes = {
        4: ('Partes de la computadora', 'Reconoce los componentes principales'),
        5: ('Internet seguro', 'Navegación responsable y protección de datos'),
        6: ('Presentaciones digitales', 'Diseña una presentación paso a paso'),
    }
    next_class_title, next_class_description = next_classes.get(
        int(grade),
        ('Herramientas digitales', 'Continúa practicando tus competencias'),
    )

    student_risk = build_student_risk_payload(student_id)
    materials = fetch_all_materials_for_student(student_id, grade, section)
    from services.adaptive_recommendations_service import build_adaptive_recommendations
    from services.adaptive_learning_service import build_adaptive_learning_profile
    adaptive_data = build_adaptive_recommendations(student_id)
    adaptive_learning = build_adaptive_learning_profile(student_id)

    return render_template(
        'student_dashboard.html',
        grade=grade,
        topics=topics,
        progress=progress,
        recommendations=recommendations,
        adaptive_data=adaptive_data,
        adaptive_learning=adaptive_learning,
        last_topic=last_topic,
        student_name=student_name,
        unread_messages=get_unread_messages_count(student_id),
        next_class_title=next_class_title,
        next_class_description=next_class_description,
        recent_activities=recent_activities,
        student_risk=student_risk,
        materials=materials,
    )


@student_blueprint.route('/api/topics', methods=['GET'])
def api_student_topics():
    denied = _auth_check()
    if denied:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    topics = fetch_topics_for_grade(session.get('user_grade') or 5, _current_student_section())
    return jsonify({'success': True, 'topics': topics})


@student_blueprint.route('/api/topics/<int:topic_id>/lesson', methods=['GET'])
def api_topic_lesson(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    grade = session.get('user_grade') or 5
    topic = next((item for item in fetch_topics_for_grade(grade, _current_student_section()) if int(item.get('id')) == topic_id), None)
    if not topic or str(topic.get('status') or '').strip() == 'Privado':
        return jsonify({'error': 'Tema no disponible para tu grado'}), 404
    student = fetch_student_by_id(session.get('student_id', 1)) or {}
    progress = fetch_student_progress(session.get('student_id', 1))
    return jsonify({'success': True, 'lesson': build_topic_lesson(
        topic, grade,
        student.get('first_name', session.get('student_name', 'Estudiante')),
        progress.get('average_grade', 0),
    )})


@student_blueprint.route('/api/topics/<int:topic_id>/materials', methods=['GET'])
def api_topic_materials(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'La clase aún no está publicada para tu grado', 'success': False}), 404
    materials = fetch_learning_materials(topic_id, session.get('student_id', 1))
    from services.db_service import fetch_topic_learning_items
    return jsonify({'success': True, 'materials': materials, 'items': fetch_topic_learning_items(topic_id)})


@student_blueprint.route('/api/topics/<int:topic_id>/practical-activity', methods=['GET'])
def api_student_practical_activity(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'La clase aún no está publicada para tu grado', 'success': False}), 404

    student_id = int(session.get('student_id', 1))
    materials = fetch_learning_materials(topic_id, student_id)
    submissions = fetch_submissions(student_id=student_id, topic_id=topic_id)
    return jsonify({
        'success': True,
        'materials': materials,
        'submissions': [
            {
                'id': submission['id'],
                'title': submission['title'],
                'file_name': submission['file_name'],
                'status': submission['status'],
                'teacher_score': submission.get('teacher_score'),
                'teacher_feedback': submission.get('teacher_feedback') or '',
                'submitted_at': submission.get('submitted_at'),
                'reviewed_at': submission.get('reviewed_at'),
            }
            for submission in submissions
        ],
    })


@student_blueprint.route('/api/topics/<int:topic_id>/learning-items', methods=['GET'])
def api_student_learning_items(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'La clase aún no está publicada para tu grado', 'success': False}), 404
    from services.db_service import fetch_topic_learning_items
    return jsonify({'success': True, 'items': fetch_topic_learning_items(topic_id)})


@student_blueprint.route('/api/materials', methods=['GET'])
def api_all_student_materials():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    student_id = session.get('student_id', 1)
    grade = session.get('user_grade')
    materials = fetch_all_materials_for_student(student_id, grade, _current_student_section())
    return jsonify({'success': True, 'materials': materials, 'total': len(materials)})


@student_blueprint.route('/api/materials/<int:material_id>', methods=['GET'])
def api_get_single_material(material_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    if request.args.get('source') == 'presentation':
        presentation = fetch_presentation_by_id(material_id)
        material = ({
            **presentation,
            'resource_url': f'/student/api/presentations/{material_id}/file',
            'source': 'presentation',
            'material_type': 'presentacion',
            'content': '',
        } if presentation else None)
    else:
        material = fetch_material_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material no encontrado', 'success': False}), 404
    if not _published_topic_for_student(material.get('topic_id')):
        return jsonify({'error': 'Material no disponible para tu grado', 'success': False}), 404
    if str(material.get('status') or 'PUBLISHED').upper() != 'PUBLISHED':
        return jsonify({'error': 'El material aún no está publicado', 'success': False}), 404

    material_type = (material.get('material_type') or '').lower()
    source = (material.get('source') or '').lower()
    if source == 'presentation' or material_type == 'presentacion':
        file_url = material.get('resource_url') or ''
        extension = os.path.splitext(material.get('file_name') or file_url.split('?', 1)[0])[1].lower()
        material['file_extension'] = extension.lstrip('.')
        if extension in ('.pptx', '.docx'):
            try:
                extracted = MaterialExtractorService.extract_from_presentation_record(
                    material,
                    require_content=False,
                )
                material['content'] = extracted.get('raw_text') or ''
            except (FileNotFoundError, ValueError, OSError) as exc:
                material['read_error'] = str(exc)
    material['snippet'] = (material.get('content') or material.get('description') or '')[:140]
    return jsonify({'success': True, 'material': material})


@student_blueprint.route('/api/materials/<int:material_id>/practice', methods=['GET'])
def api_get_material_practice(material_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    is_presentation = request.args.get('source') == 'presentation'
    presentation = fetch_presentation_by_id(material_id) if is_presentation else None
    material = ({
        **presentation,
        'resource_url': f'/student/api/presentations/{material_id}/file',
        'source': 'presentation',
        'material_type': 'presentacion',
        'content': '',
    } if presentation else None) if is_presentation else fetch_material_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material no encontrado', 'success': False}), 404
    if not _published_topic_for_student(material.get('topic_id')):
        return jsonify({'error': 'Material no disponible para tu grado', 'success': False}), 404
    if str(material.get('status') or 'PUBLISHED').upper() != 'PUBLISHED':
        return jsonify({'error': 'El material aún no está publicado', 'success': False}), 404

    if is_presentation:
        extracted = MaterialExtractorService.extract_from_presentation_record(material)
        text = extracted.get('raw_text') or ''
    else:
        text = material.get('content') or material.get('description') or ''
    title = material.get('title') or 'Material'
    grade = session.get('user_grade') or material.get('grade') or 5

    scope = f"{'presentation' if is_presentation else 'material'}:{material_id}"
    ai_pack = get_practice(scope, text, title, int(grade))
    try:
        attempt = start_attempt(session['student_id'], material['topic_id'], 'practice', scope, ai_pack.get('questions', []))
    except AttemptError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 409
    return jsonify({
        'success': True,
        'material_id': material_id,
        'material_title': title,
        'topic_id': material.get('topic_id'),
        'topic_title': material.get('topic_title'),
        **public_attempt(attempt),
        'activities': [],
        'source': ai_pack.get('source', 'ai'),
    })


@student_blueprint.route('/api/materials/<int:material_id>/practice', methods=['POST'])
def api_submit_material_practice(material_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    is_presentation = request.args.get('source') == 'presentation'
    presentation = fetch_presentation_by_id(material_id) if is_presentation else None
    material = ({
        **presentation,
        'resource_url': f'/student/api/presentations/{material_id}/file',
        'source': 'presentation',
        'material_type': 'presentacion',
        'content': '',
    } if presentation else None) if is_presentation else fetch_material_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material no encontrado', 'success': False}), 404
    if not _published_topic_for_student(material.get('topic_id')):
        return jsonify({'error': 'Material no disponible para tu grado', 'success': False}), 404
    if str(material.get('status') or 'PUBLISHED').upper() != 'PUBLISHED':
        return jsonify({'error': 'El material aún no está publicado', 'success': False}), 404

    data = request.get_json(silent=True) or {}
    scope = f"{'presentation' if is_presentation else 'material'}:{material_id}"
    try:
        uuid.UUID(str(data.get('attempt_id', '')))
        result = submit_attempt(data['attempt_id'], session['student_id'], 'practice', scope, data.get('answers', {}))
    except (AttemptError, ValueError) as exc:
        return jsonify({'success': False, 'error': str(exc)}), 409
    if not is_presentation:
        mark_material_reviewed(material_id, session['student_id'])
    return jsonify({'success': True, 'material_id': material_id, **result})


@student_blueprint.route('/api/materials/<int:material_id>/reviewed', methods=['POST'])
def api_mark_material_reviewed(material_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    source = request.args.get('source', 'material')
    if source == 'presentation':
        material = fetch_presentation_by_id(material_id)
    elif source == 'material':
        material = fetch_material_by_id(material_id)
    else:
        return jsonify({'success': False, 'error': 'Tipo de material no válido'}), 400
    if (
        not material
        or str(material.get('status') or 'PUBLISHED').upper() != 'PUBLISHED'
        or not _published_topic_for_student(material.get('topic_id'))
    ):
        return jsonify({'success': False, 'error': 'Material no disponible para tu grado y sección'}), 404
    mark_material_reviewed(material_id, session.get('student_id', 1), source=source)
    return jsonify({'success': True})



@student_blueprint.route('/api/topics/<int:topic_id>/activity', methods=['POST'])
def api_submit_activity(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'La clase aún no está publicada para tu grado'}), 404
    data = request.get_json() or {}
    if data.get('activity_type', 'actividades') not in {'actividades', 'juegos'}:
        return jsonify({'success': False, 'error': 'Los exámenes deben enviarse desde su intento formal.'}), 400
    result = grade_activity(
        student_id=session.get('student_id', 1),
        topic_id=topic_id,
        answers=data.get('answers', {}),
        started_at=data.get('started_at'),
        activity_type=data.get('activity_type', 'actividades'),
    )
    return jsonify({'success': True, 'result': result})


@student_blueprint.route('/api/topics/<int:topic_id>/submission', methods=['POST'])
def api_submit_topic_work(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'El tema no está publicado para tu grado y sección'}), 404
    uploaded_file = request.files.get('file')
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({'error': 'Selecciona un archivo para entregar'}), 400
    filename = secure_filename(uploaded_file.filename)
    if not filename:
        return jsonify({'error': 'El nombre del archivo no es válido'}), 400
    allowed_extensions = {
        'pdf', 'doc', 'docx', 'odt', 'ppt', 'pptx', 'xls', 'xlsx', 'csv', 'txt',
        'png', 'jpg', 'jpeg', 'mp4', 'mov', 'webm', 'mp3', 'zip',
    }
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in allowed_extensions:
        return jsonify({'error': 'Formato no permitido. Usa PDF, Office, imagen o ZIP.'}), 400
    max_file_size = 20 * 1024 * 1024
    if request.content_length and request.content_length > max_file_size + 1024 * 1024:
        return jsonify({'error': 'El archivo supera el límite de 20 MB'}), 413

    student_id = int(session.get('student_id', 1))
    upload_dir = current_app.config.get(
        'STUDENT_SUBMISSION_DIR',
        os.path.join(current_app.root_path, 'static', 'uploads', 'student_work'),
    )
    try:
        uploaded_file.stream.seek(0, os.SEEK_END)
        file_size = uploaded_file.stream.tell()
        uploaded_file.stream.seek(0)
    except (AttributeError, OSError, ValueError):
        file_size = uploaded_file.content_length or 0
    if file_size > max_file_size:
        return jsonify({'error': 'El archivo supera el límite de 20 MB'}), 413
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f'{student_id}_{topic_id}_{uuid.uuid4().hex}_{filename[:180]}'
    stored_path = os.path.join(upload_dir, stored_name)
    uploaded_file.save(stored_path)
    try:
        from services.file_storage_service import store_bytes
        from pathlib import Path
        store_bytes(f'/static/uploads/student_work/{stored_name}', Path(stored_path).read_bytes())
        submission_id = create_student_submission(
            student_id, topic_id, (request.form.get('title') or 'Trabajo del tema').strip()[:255] or 'Trabajo del tema',
            f'/static/uploads/student_work/{stored_name}', filename,
        )
    except Exception:
        if os.path.exists(stored_path):
            os.remove(stored_path)
        raise
    return jsonify({'success': True, 'submission_id': submission_id, 'message': 'Trabajo enviado al profesor'}), 201


@student_blueprint.route('/api/topics/<int:topic_id>/submissions', methods=['GET'])
def api_student_topic_submissions(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'El tema no está publicado para tu grado y sección'}), 404
    submissions = fetch_submissions(
        student_id=int(session.get('student_id', 1)),
        topic_id=topic_id,
    )
    return jsonify({
        'success': True,
        'submissions': [
            {
                'id': submission['id'],
                'title': submission['title'],
                'file_name': submission['file_name'],
                'status': submission['status'],
                'teacher_score': submission.get('teacher_score'),
                'teacher_feedback': submission.get('teacher_feedback') or '',
                'submitted_at': submission.get('submitted_at'),
                'reviewed_at': submission.get('reviewed_at'),
            }
            for submission in submissions
        ],
    })


@student_blueprint.route('/api/topics/<int:topic_id>/personalized-game', methods=['GET'])
def api_personalized_game(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    grade = session.get('user_grade') or 5
    topic = fetch_topic_by_id(topic_id)
    if not topic:
        topic = next((item for item in fetch_topics_for_grade(grade) if int(item.get('id')) == topic_id), None)
    if not topic or not _published_topic_for_student(topic_id):
        return jsonify({'error': 'Tema no encontrado'}), 404
    student_id = session.get('student_id', 1)
    student = fetch_student_by_id(student_id) or {}
    progress = fetch_student_progress(student_id)
    pack = generate_student_learning_pack(
        topic.get('title', 'Tema'), grade,
        student.get('first_name', session.get('student_name', 'Estudiante')),
        progress.get('average_grade', 0),
    )
    return jsonify({'success': True, 'source': pack.get('source'), 'game': pack['game']})


@student_blueprint.route('/api/topics/<int:topic_id>/evaluation', methods=['GET', 'POST'])
def api_topic_evaluation(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    topic = _published_topic_for_student(topic_id)
    if not topic:
        return jsonify({'error': 'Evaluación no encontrada para este tema'}), 404
    # GOAL 3: Verificar aprobación docente y estado de publicación
    all_topic_assessments = fetch_assessments_for_topic(topic_id)
    published_assessment = fetch_published_assessment_for_topic(topic_id)
    latest_assessment = all_topic_assessments[0] if all_topic_assessments else None
    if latest_assessment and latest_assessment.get('status') != 'PUBLISHED':
        published_assessment = None

    if request.method == 'GET':
        # Si existe evaluación pero está en GENERATED, PENDING_REVIEW o APPROVED (no publicada)
        if all_topic_assessments and not published_assessment:
            return jsonify({
                'success': False,
                'status': 'NOT_PUBLISHED',
                'published': False,
                'error': 'La evaluación de este tema está siendo revisada por el profesor y aún no ha sido publicada.',
            }), 403

        # Si hay evaluación publicada, retornar EXCLUSIVAMENTE las preguntas aprobadas
        if published_assessment:
            approved_questions = [
                {
                    'id': q['id'],
                    'question': q['question'],
                    'options': q.get('options') or [q.get('option_a'), q.get('option_b'), q.get('option_c')],
                    'subtopic': q.get('subtopic'),
                    'score': 2,
                    'approved': True,
                }
                for q in published_assessment.get('questions', [])
                if q.get('approved')
            ]
            if not approved_questions:
                return jsonify({
                    'success': False,
                    'status': 'NO_APPROVED_QUESTIONS',
                    'published': False,
                    'error': 'La evaluación aún no contiene preguntas aprobadas por el profesor.',
                }), 403

            try:
                attempt = start_attempt(session['student_id'], topic_id, 'exam', str(published_assessment['id']),
                                        [dict(q) for q in published_assessment.get('questions', []) if q.get('approved')],
                                        published_assessment['id'])
            except AttemptError as exc:
                return jsonify({'success': False, 'error': str(exc)}), 409
            frozen = public_attempt(attempt)
            formal_questions = frozen['questions']

            return jsonify({
                'success': True,
                'status': 'PUBLISHED',
                'published': True,
                'evaluation': {
                    **frozen,
                    'assessment_id': published_assessment.get('id'),
                    'topic_id': topic_id,
                    'title': published_assessment.get('title') or f"Evaluación Final: {topic.get('title', 'Tema')}",
                    'difficulty': 'media',
                    'duration_minutes': 30,
                    'questions': formal_questions,
                    'total_questions': len(formal_questions),
                    'source': 'approved_teacher_evaluation',
                }
            }), 200

        # Si no existe ningún assessment en el sistema para este tema
        return jsonify({
            'success': False,
            'status': 'NOT_PUBLISHED',
            'published': False,
            'error': 'El profesor aún no ha aprobado ni publicado una evaluación para este tema.',
        }), 404

    data = request.get_json(silent=True) or {}
    if not published_assessment:
        return jsonify({'success': False, 'error': 'El examen no está publicado.'}), 403
    try:
        uuid.UUID(str(data.get('attempt_id', '')))
        result = submit_attempt(data['attempt_id'], session['student_id'], 'exam', str(published_assessment['id']), data.get('answers', {}))
    except (AttemptError, ValueError) as exc:
        return jsonify({'success': False, 'error': str(exc)}), 409
    result['recommended_games'] = detect_weaknesses_and_recommend_games(session['student_id'], result.get('reinforce_topics'))
    return jsonify({'success': True, 'attempt_id': result.get('assessment_attempt_id'),
                    'learning_attempt_id': data['attempt_id'], 'result': result})


@student_blueprint.route('/api/assessments/attempts', methods=['GET'])
def api_student_assessment_attempts():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    student_id = session.get('student_id', 1)
    assessment_id = request.args.get('assessment_id')
    attempts = fetch_student_assessment_attempts(
        student_id,
        int(assessment_id) if assessment_id else None
    )
    return jsonify({
        'success': True,
        'attempts': attempts,
        'total': len(attempts),
    }), 200


# =========================================================================
# GOAL 5: Juegos Interactivos de Reforzamiento (Práctica antes del Examen)
# =========================================================================

@student_blueprint.route('/api/reinforcement-games', methods=['GET'])
def api_get_reinforcement_games():
    """
    Retorna el catálogo de juegos interactivos de reforzamiento.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    games = get_all_reinforcement_games()
    return jsonify({
        'success': True,
        'games': games,
        'total': len(games),
    }), 200


@student_blueprint.route('/api/reinforcement-games/<int:game_id>', methods=['GET'])
def api_get_reinforcement_game_detail(game_id):
    """
    Retorna el detalle de un juego de reforzamiento específico.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    game = get_reinforcement_game(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    safe_game = dict(game)
    safe_game.pop('correct_answer', None)
    safe_game.pop('acceptable_answers', None)
    return jsonify({
        'success': True,
        'game': safe_game,
    }), 200


@student_blueprint.route('/api/reinforcement-games/<int:game_id>/play', methods=['POST'])
def api_play_reinforcement_game(game_id):
    """
    Envía y califica el intento del estudiante para un juego de reforzamiento,
    persistiendo el resultado en student_game_attempts y sincronizando en student_notes.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    game = get_reinforcement_game(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    student_id = int(session.get('student_id', 1))
    payload = request.get_json() or {}
    student_answer = payload.get('answer')
    time_spent = int(payload.get('time_spent') or 10)

    if student_answer is None or str(student_answer).strip() == '':
        return jsonify({'error': 'Debes seleccionar o escribir una respuesta', 'success': False}), 400

    eval_result = evaluate_game_submission(game, student_answer, time_spent)

    # 1. Guardar intento en la tabla requerida: student_game_attempts
    attempt_id = record_student_game_attempt(
        student_id=student_id,
        game_id=game['id'],
        topic_id=int(game.get('topic_id', 1)),
        game_type=game.get('game_type', 'opcion_multiple'),
        score=eval_result['score'],
        is_correct=eval_result['is_correct'],
        student_answer=eval_result['student_answer'],
        time_spent=time_spent,
    )

    # 2. Sincronizar en student_notes para alimentar métricas de progreso (games_count) y ML


    return jsonify({
        'success': True,
        'attempt_id': attempt_id,
        'result': eval_result,
        'game': {
            'id': game['id'],
            'title': game['title'],
            'game_type': game['game_type'],
            'topic_title': game['topic_title'],
        }
    }), 200


@student_blueprint.route('/api/reinforcement-games/recommendations', methods=['GET'])
def api_get_reinforcement_game_recommendations():
    """
    Retorna juegos de reforzamiento recomendados según debilidades detectadas.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    student_id = int(session.get('student_id', 1))
    topic_filter = request.args.get('topic')
    explicit_topics = [topic_filter] if topic_filter else None

    recommended = detect_weaknesses_and_recommend_games(student_id, explicit_topics)
    return jsonify({
        'success': True,
        'recommendations': recommended,
        'total': len(recommended),
    }), 200


@student_blueprint.route('/api/reinforcement-games/attempts', methods=['GET'])
def api_get_student_game_attempts():
    """
    Retorna el historial de juegos practicados por el estudiante.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    student_id = int(session.get('student_id', 1))
    game_id = request.args.get('game_id')
    attempts = fetch_student_game_attempts(
        student_id,
        int(game_id) if game_id else None
    )
    return jsonify({
        'success': True,
        'attempts': attempts,
        'total': len(attempts),
    }), 200


# =========================================================================
# Juegos Educativos Generados por IA con Aprobación Docente (GOAL Ollama)
# =========================================================================

@student_blueprint.route('/api/topics/<int:topic_id>/ai-games', methods=['GET'])
def api_get_topic_ai_games(topic_id):
    """
    Retorna ÚNICAMENTE los juegos generados por IA que están en estado PUBLISHED.
    El estudiante jamás tiene acceso a juegos en borrador ni pendientes.
    Las respuestas correctas son removidas del JSON para evitar trampas.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'El juego no está disponible para tu grado', 'success': False}), 404

    games = fetch_published_ai_games_for_topic(topic_id)
    safe_games = []
    for g in games:
        item = dict(g)
        raw_content = dict(item.get('content_json') or {})
        game_type = GameEngine.normalize_type(item.get('game_type'))

        safe_content = dict(raw_content)
        if game_type == 'multiple_choice':
            safe_content.pop('answer', None)
        elif game_type == 'true_false':
            safe_content.pop('correct_answer', None)
        elif game_type == 'fill_blank':
            safe_content.pop('answers', None)
            safe_content.pop('blank_word', None)
        elif game_type == 'matching':
            pairs = list(raw_content.get('pairs') or [])
            lefts = [p.get('left') for p in pairs if isinstance(p, dict)]
            rights = [p.get('right') for p in pairs if isinstance(p, dict)]
            import random
            shuffled_rights = rights[:]
            random.seed(int(item.get('id', 1)) + 42)
            random.shuffle(shuffled_rights)
            safe_content['left_items'] = lefts
            safe_content['right_items'] = shuffled_rights
            safe_content.pop('pairs', None)
        elif game_type == 'memory':
            pairs = list(raw_content.get('pairs') or [])
            cards = []
            for pair_index, pair in enumerate(pairs):
                if isinstance(pair, dict):
                    cards.extend([
                        {'pair_id': pair_index, 'side': 'left', 'text': pair.get('left', '')},
                        {'pair_id': pair_index, 'side': 'right', 'text': pair.get('right', '')},
                    ])
            safe_content['cards'] = cards
            safe_content.pop('pairs', None)
        elif game_type == 'ordering':
            import random
            items = list(raw_content.get('items') or [])
            random.Random(int(item.get('id', 1)) + 91).shuffle(items)
            safe_content['items'] = items
        elif game_type == 'drag_drop':
            safe_content['items'] = [entry.get('item', '') for entry in raw_content.get('items', []) if isinstance(entry, dict)]
        elif game_type == 'challenge':
            levels = []
            for level in raw_content.get('levels', []):
                if isinstance(level, dict):
                    clean_level = dict(level)
                    clean_level.pop('answer', None)
                    levels.append(clean_level)
            safe_content['levels'] = levels

        safe_content.pop('explanation', None)
        item['content'] = safe_content
        item['content_json'] = safe_content
        safe_games.append(item)

    return jsonify({
        'success': True,
        'topic_id': topic_id,
        'games': safe_games,
        'total': len(safe_games),
    }), 200


@student_blueprint.route('/api/ai-games/<int:game_id>/play', methods=['POST'])
def api_play_ai_game(game_id):
    """
    Evalúa el intento del alumno en un juego generado por IA,
    devuelve retroalimentación interactiva infantil ("¡Correcto! 🎉 +10 puntos" o "¡Casi! Inténtalo de nuevo 💪"),
    persiste el intento en student_game_attempts y actualiza notas en student_notes.
    """
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    game = fetch_ai_generated_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    # Regla estricta: Solo juegos PUBLISHED
    if game.get('status') != 'PUBLISHED':
        return jsonify({
            'error': 'Este juego aún no ha sido aprobado ni publicado por el docente.',
            'success': False,
        }), 403

    if not _published_topic_for_student(game.get('topic_id')):
        return jsonify({'error': 'Este juego no está disponible para tu grado', 'success': False}), 403

    payload = request.get_json() or {}
    student_answer = payload.get('answer')
    time_spent = int(payload.get('time_spent') or 10)

    if student_answer is None and not any(key in payload for key in ('matches', 'order', 'placements', 'answers')):
        return jsonify({'error': 'Debes enviar una respuesta', 'success': False}), 400

    content = game.get('content_json') or {}
    game_metadata = content.get('_meta') or {}
    game_type = game.get('game_type')
    is_correct = False
    completion_ratio = 0.0
    explanation = content.get('explanation') or "¡Sigue repasando el tema para convertirte en un experto!"

    game_type = GameEngine.normalize_type(game_type)
    is_correct, completion_ratio = GameEngine.score_attempt(game_type, content, payload)

    # Experiencia de retroalimentación infantil
    student_id = int(session.get('student_id', 1))
    topic_id = int(game.get('topic_id', 1))

    if is_correct:
        points_earned = 10
        score_val = 20.0
        feedback_headline = "¡Correcto! 🎉 +10 puntos"
        feedback_sub = game_metadata.get('feedback_correct') or "¡Excelente respuesta! Demostraste un gran dominio del tema."
        badge_class = "success"
    else:
        points_earned = 0
        score_val = 5.0
        feedback_headline = "¡Casi! Inténtalo de nuevo 💪"
        feedback_sub = game_metadata.get('feedback_wrong') or "¡No te preocupes! Lee con atención la explicación y supéralo en el próximo intento."
        badge_class = "warning"

    # Persistir intento
    attempt_id = record_student_ai_game_attempt(
        student_id=student_id,
        game_id=game['id'],
        topic_id=topic_id,
        game_type=game_type,
        score=score_val,
        is_correct=is_correct,
        student_answer=str(student_answer)[:255] if student_answer is not None else "matching_pairs",
        time_spent=time_spent,
    )



    return jsonify({
        'success': True,
        'attempt_id': attempt_id,
        'is_correct': is_correct,
        'points_earned': points_earned,
        'feedback_headline': feedback_headline,
        'feedback_sub': feedback_sub,
        'explanation': explanation,
        'badge_class': badge_class,
        'game_id': game['id'],
        'game_title': game['title'],
        'completion_ratio': completion_ratio,
        'learning_objective': game_metadata.get('learning_objective', ''),
        'score': score_val,
    }), 200


@student_blueprint.route('/api/progress', methods=['GET'])
def api_student_progress():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    student_id = session.get('student_id', 1)
    topics = fetch_topics_for_grade(session.get('user_grade') or 5, _current_student_section())
    progress = build_student_progress(student_id, topics)
    return jsonify({'success': True, 'progress': progress})


@student_blueprint.route('/api/recommendations', methods=['GET'])
def api_student_recommendations():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    student_id = session.get('student_id', 1)
    from services.adaptive_recommendations_service import build_adaptive_recommendations
    adaptive_data = build_adaptive_recommendations(student_id)
    return jsonify({
        'success': True,
        'student_diagnosis': adaptive_data.get('student_diagnosis'),
        'primary_topic': adaptive_data.get('primary_topic'),
        'headline': adaptive_data.get('headline'),
        'actions': adaptive_data.get('actions'),
        'recommendations': adaptive_data.get('recommendations'),
    })


@student_blueprint.route('/api/adaptive-learning', methods=['GET'])
def api_student_adaptive_learning():
    """Entrenamiento personalizado: solamente enlaza material o juegos ya publicados."""
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401
    from services.adaptive_learning_service import build_adaptive_learning_profile
    return jsonify({'success': True, 'training': build_adaptive_learning_profile(session.get('student_id', 1))}), 200


@student_blueprint.route('/api/ollama-games', methods=['GET'])
def api_ollama_games():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401
    grade = int(session.get('user_grade') or 5)
    games = fetch_all_games_with_topics()
    section = _current_student_section()
    visible_games = [
        game for game in games
        if int(game.get('grade') or 0) == grade
        and (not game.get('section') or str(game.get('section')).upper() == section)
    ]
    unique_games = []
    seen_topics = set()
    for game in visible_games:
        topic_id = game.get('topic_id')
        if topic_id in seen_topics:
            continue
        seen_topics.add(topic_id)
        unique_games.append(game)
    return jsonify({'success': True, 'games': unique_games})


@student_blueprint.route('/topics')
def student_topics():
    denied = _auth_check()
    if denied:
        return denied
    return redirect(url_for('student.student_home'))


@student_blueprint.route('/progress')
def student_progress():
    denied = _auth_check()
    if denied:
        return denied
    return redirect(url_for('student.student_home'))


@student_blueprint.route('/api/presentations/<int:topic_id>', methods=['GET'])
def api_get_presentations(topic_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    if not _published_topic_for_student(topic_id):
        return jsonify({'error': 'La sesión no está publicada para tu grado y sección', 'success': False}), 404
    presentations = get_presentations_for_topic(topic_id, published_only=True)
    return jsonify({'presentations': presentations, 'success': True})


@student_blueprint.route('/api/presentations/<int:presentation_id>/file', methods=['GET'])
def api_student_presentation_file(presentation_id):
    denied = _auth_check()
    if denied:
        return denied
    presentation = fetch_presentation_by_id(presentation_id)
    if (
        not presentation
        or str(presentation.get('status') or 'PUBLISHED').upper() != 'PUBLISHED'
        or not _published_topic_for_student(presentation.get('topic_id'))
    ):
        return jsonify({'error': 'La presentación no está publicada para tu grado y sección'}), 404
    try:
        response = send_presentation_file(
            presentation.get('file_path'),
            presentation.get('file_name') or 'presentacion',
        )
        mark_material_reviewed(presentation_id, session.get('student_id', 1), source='presentation')
        return response
    except FileNotFoundError:
        return jsonify({'error': 'No se encontró el archivo de la presentación'}), 404


@student_blueprint.route('/api/messages', methods=['GET'])
def api_get_messages():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    student_id = session.get('student_id', 1)
    try:
        messages = fetch_messages_for_student(int(student_id))
        return jsonify({'success': True, 'messages': messages, 'total': len(messages)}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al obtener mensajes: {str(exc)}'}), 500


@student_blueprint.route('/api/messages/<int:message_id>/read', methods=['PUT'])
def api_mark_message_read(message_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        mark_message_as_read(message_id)
        return jsonify({'success': True, 'message': 'Mensaje marcado como leído'}), 200
    except Exception as exc:
        return jsonify({'error': f'Error: {str(exc)}'}), 500


@student_blueprint.route('/api/alerts', methods=['GET'])
def api_get_alerts():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    student_id = session.get('student_id', 1)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    try:
        alerts = fetch_alerts_for_user(student_id=int(student_id), unread_only=unread_only)
        return jsonify({'success': True, 'alerts': alerts, 'total': len(alerts)}), 200
    except Exception as exc:
        return jsonify({'error': f'Error al obtener alertas: {str(exc)}'}), 500


@student_blueprint.route('/api/alerts/<int:alert_id>/read', methods=['PUT'])
def api_mark_alert_read(alert_id):
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        mark_alert_as_read(alert_id)
        return jsonify({'success': True, 'message': 'Alerta marcada como leída'}), 200
    except Exception as exc:
        return jsonify({'error': f'Error: {str(exc)}'}), 500


@student_blueprint.route('/api/risk-prediction', methods=['GET'])
def api_student_risk_prediction():
    denied = _auth_check()
    if denied:
        return jsonify({'error': 'No autorizado', 'success': False}), 401

    student_id = session.get('student_id')
    if not student_id:
        return jsonify({'error': 'Sesión de estudiante no válida', 'success': False}), 401

    # Prevención IDOR: Un estudiante solo puede consultar su propia predicción
    requested_student_id = request.args.get('student_id')
    if requested_student_id is not None and str(requested_student_id) != str(student_id):
        return jsonify({
            'error': 'No autorizado para consultar la predicción de otro alumno',
            'success': False,
            'code': 'FORBIDDEN',
        }), 403

    payload = build_student_risk_payload(int(student_id))
    return jsonify(payload), 200
