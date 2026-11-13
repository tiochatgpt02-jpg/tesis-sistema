from flask import Blueprint, jsonify, render_template, request, session
from services.grading_policy_service import get_policy, save_policy
from services.learning_attempt_service import reopen_exam
from services import db_service

settings_blueprint = Blueprint('settings', __name__, url_prefix='/teacher')


@settings_blueprint.route('/api/<source>/<int:material_id>/prepare-practice', methods=['POST'])
def api_prepare_practice(source, material_id):
    from services.material_extractor_service import MaterialExtractorService
    from services.ai_service import generate_questions_from_teacher_material
    from services.practice_service import save_practice
    if source == 'presentations':
        material = db_service.fetch_presentation_by_id(material_id)
        if not material:
            return jsonify({'success': False, 'error': 'Material no encontrado.'}), 404
        try:
            text = MaterialExtractorService.extract_from_presentation_record(material).get('raw_text') or ''
        except (OSError, ValueError) as exc:
            return jsonify({'success': False, 'error': str(exc)}), 400
        kind = 'presentation'
    elif source == 'materials':
        material = db_service.fetch_material_by_id(material_id)
        if not material:
            return jsonify({'success': False, 'error': 'Material no encontrado.'}), 404
        text = material.get('content') or material.get('description') or ''
        kind = 'material'
    else:
        return jsonify({'success': False, 'error': 'Fuente no válida.'}), 404
    topic = db_service.fetch_topic_by_id(material['topic_id']) or {}
    grade = int(topic.get('grade') or material.get('grade') or 5)
    payload = generate_questions_from_teacher_material(text,material.get('title') or 'Material',grade=grade)
    if not payload.get('questions'):
        return jsonify({'success': False, 'error': payload.get('error') or 'No se pudieron preparar preguntas.'}), 422
    save_practice(f'{kind}:{material_id}',text,grade,payload)
    return jsonify({'success': True, 'source': payload.get('source'), 'questions': payload['questions']})


@settings_blueprint.route('/settings', methods=['GET', 'POST'])
def academic_settings():
    message = None
    if request.method == 'POST':
        try:
            save_policy(request.form.get('practice_weight'), request.form.get('exam_weight'))
            message = 'Pesos guardados. Los juegos no afectan las notas.'
        except (ValueError, TypeError) as exc:
            return render_template('academic_settings.html', policy=get_policy(), message=str(exc)), 400
    return render_template('academic_settings.html', policy=get_policy(), message=message)


@settings_blueprint.route('/api/assessments/<int:assessment_id>/students/<int:student_id>/reopen', methods=['POST'])
def api_reopen_exam(assessment_id, student_id):
    assessment = db_service.fetch_assessment_by_id(assessment_id)
    student = db_service.fetch_student_by_id(student_id)
    topic = db_service.fetch_topic_by_id(assessment.get('topic_id')) if assessment else None
    if not assessment or not student or not topic or int(topic['grade']) != int(student['grade']):
        return jsonify({'success': False, 'error': 'El examen no corresponde al grado del alumno.'}), 404
    if topic.get('section') and str(topic['section']).upper() != str(student.get('section') or 'A').upper():
        return jsonify({'success': False, 'error': 'El examen no corresponde a la sección.'}), 404
    reopen_exam(student_id, assessment_id, session['user_id'])
    return jsonify({'success': True, 'message': 'Se habilitó un nuevo intento sin borrar el historial.'})


@settings_blueprint.route('/exam-reopening', methods=['GET', 'POST'])
def reopening_form():
    message = None
    if request.method == 'POST':
        response = api_reopen_exam(int(request.form['assessment_id']), int(request.form['student_id']))
        data = response[0].get_json() if isinstance(response, tuple) else response.get_json()
        message = data.get('message') or data.get('error')
    return render_template('exam_reopening.html', students=db_service.fetch_students(),
                           assessments=db_service.fetch_all_assessments(), message=message)
