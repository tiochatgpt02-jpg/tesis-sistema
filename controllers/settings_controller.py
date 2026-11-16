from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, flash
import secrets
from services import bimester_grade_service as bimester
from services.grading_policy_service import get_policy, save_policy, save_component_policy, COMPONENTS, DEFAULT_COMPONENT_WEIGHTS
from services.learning_attempt_service import reopen_exam
from services import db_service

settings_blueprint = Blueprint('settings', __name__, url_prefix='/teacher')


@settings_blueprint.route('/bimester-grades', methods=['GET', 'POST'])
def bimester_grades():
    if session.get('user_role') != 'teacher':
        return jsonify({'error': 'No autorizado'}), 403
    default_year, default_period = bimester.current_term()
    values = request.form if request.method == 'POST' else request.args
    try:
        year, period, grade = bimester.validate_term(values.get('year', default_year), values.get('period', default_period), values.get('grade', 5))
    except ValueError as exc:
        return str(exc), 400
    token = session.get('gradebook_csrf')
    if not token:
        token = session['gradebook_csrf'] = secrets.token_urlsafe(32)
    error = None
    if request.method == 'POST':
        if not secrets.compare_digest(str(request.form.get('csrf_token') or ''), token):
            return 'La sesión del formulario venció. Recarga la página.', 403
        try:
            if request.form.get('action') == 'sources':
                bimester.save_sources(grade, year, period, request.form, session.get('user_id'))
                flash('Fuentes guardadas. Las notas vinculadas usan el último intento del bimestre.', 'success')
            elif request.form.get('action') == 'marks':
                student_id = int(request.form.get('student_id') or 0)
                student = db_service.fetch_student_by_id(student_id)
                if not student or int(student.get('grade') or 0) != grade:
                    raise ValueError('El alumno no corresponde al grado seleccionado.')
                bimester.save_marks(student_id, year, period, request.form, session.get('user_id'))
                flash('Notas del alumno guardadas.', 'success')
            elif request.form.get('action') in ('close','reopen'):
                from services.academic_closure_service import change_closure
                change_closure(grade,year,period,request.form['action'],request.form.get('reason'),session.get('user_id'))
                flash('Se actualizó el estado del bimestre y se registró el motivo.', 'success')
            else:
                raise ValueError('Acción no válida.')
            return redirect(url_for('settings.bimester_grades', grade=grade, year=year, period=period), code=303)
        except ValueError as exc:
            error = str(exc)
    students = [row for row in db_service.fetch_students() if int(row.get('grade') or 0) == grade]
    policy = get_policy()
    if not policy or policy.get('mode') != 'components':
        policy = {'mode': 'components', 'weights': DEFAULT_COMPONENT_WEIGHTS}
    rows = bimester.grade_rows(students, db_service.fetch_student_results(), year, period, policy)
    _, sources = bimester.load_entries(year, period)
    selected_sources = {row['component']: row['source_item'] for row in sources if int(row['grade']) == grade}
    from services.teacher_reports_service import period_date_range
    start, end, _ = period_date_range(str(period), year)
    from services.academic_calendar_service import get_calendar
    from services.academic_closure_service import closed_periods
    closure = closed_periods(year, period).get(grade)
    if closure:
        policy = closure['snapshot']['policy']
        start, end = closure['snapshot']['date_from'], closure['snapshot']['date_to']
    return render_template('bimester_grades.html', rows=rows, components=COMPONENTS, policy=policy,
                           options=bimester.source_options(grade), selected_sources=selected_sources,
                           grade=grade, year=year, period=period, date_from=start, date_to=end,
                           csrf_token=token, error=error, calendar_confirmed=get_calendar(year)['confirmed'], closure=closure), (400 if error else 200)


@settings_blueprint.route('/academic-calendar', methods=['GET', 'POST'])
def academic_calendar():
    if session.get('user_role') != 'teacher':
        return jsonify({'error': 'No autorizado'}), 403
    from services.academic_calendar_service import get_calendar, save_calendar, validate_year, school_today
    values = request.form if request.method == 'POST' else request.args
    try:
        year = validate_year(values.get('year', school_today().year))
    except ValueError as exc:
        return str(exc), 400
    token = session.setdefault('calendar_csrf', secrets.token_urlsafe(32))
    error = None
    if request.method == 'POST':
        if not secrets.compare_digest(str(request.form.get('csrf_token') or ''), token):
            return 'La sesión del formulario venció. Recarga la página.', 403
        try:
            periods = [{'date_from': request.form.get(f'start_{number}'), 'date_to': request.form.get(f'end_{number}')}
                       for number in range(1, 5)]
            save_calendar(year, periods, request.form.get('confirmed') == 'yes', session.get('user_id'))
            flash('Calendario guardado.', 'success')
            return redirect(url_for('settings.academic_calendar', year=year), code=303)
        except ValueError as exc:
            error = str(exc)
    return render_template('academic_calendar.html', calendar=get_calendar(year), csrf_token=token, error=error), (400 if error else 200)


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
            save_component_policy({key: request.form.get(key) for key, _ in COMPONENTS})
            message = 'Pesos guardados. Los juegos no afectan las notas.'
        except (ValueError, TypeError) as exc:
            return render_template('academic_settings.html', policy=get_policy(), components=COMPONENTS,
                                   defaults=DEFAULT_COMPONENT_WEIGHTS, message=str(exc)), 400
    return render_template('academic_settings.html', policy=get_policy(), components=COMPONENTS,
                           defaults=DEFAULT_COMPONENT_WEIGHTS, message=message)


@settings_blueprint.route('/api/assessments/<int:assessment_id>/students/<int:student_id>/reopen', methods=['POST'])
def api_reopen_exam(assessment_id, student_id):
    assessment = db_service.fetch_assessment_by_id(assessment_id)
    if assessment and assessment.get('kind', 'exam') != 'exam':
        return jsonify({'success': False, 'error': 'Las prácticas permiten nuevos intentos y no requieren reapertura.'}), 400
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
                           assessments=[row for row in db_service.fetch_all_assessments() if row.get('kind', 'exam') == 'exam'], message=message)
