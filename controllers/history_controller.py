from flask import Blueprint, jsonify, render_template, request, session
from services.literal_history_service import DIMENSIONS, fetch_history, readiness
from services.academic_calendar_service import school_today

history_blueprint = Blueprint('institutional_history', __name__)


@history_blueprint.route('/teacher/institutional-history')
def teacher_history():
    if session.get('user_role') != 'teacher' or not session.get('is_authenticated'):
        return jsonify({'error': 'No autorizado'}), 403
    try:
        grade = int(request.args.get('grade', 4))
        year = int(request.args.get('year', school_today().year))
        period = int(request.args.get('period', 1))
        if grade not in (4, 5, 6) or not 2000 <= year <= 2100 or period not in (1, 2, 3, 4):
            raise ValueError()
    except ValueError:
        return 'Selecciona un grado, año y bimestre válidos.', 400
    records = fetch_history(grade=grade, year=year, period=period)
    return render_template('institutional_history.html', records=records, dimensions=DIMENSIONS,
                           status=readiness(), grade=grade, year=year, period=period, teacher=True)


@history_blueprint.route('/teacher/api/institutional-history/status')
def institutional_status():
    if session.get('user_role') != 'teacher' or not session.get('is_authenticated'):
        return jsonify({'error': 'No autorizado'}), 403
    return jsonify(readiness())


@history_blueprint.route('/student/institutional-history')
def student_history():
    if session.get('user_role') != 'student' or not session.get('is_authenticated') or not session.get('student_id'):
        return jsonify({'error': 'No autorizado'}), 403
    records = fetch_history(student_id=session['student_id'])
    return render_template('institutional_history.html', records=records, dimensions=DIMENSIONS,
                           teacher=False, status=None)


@history_blueprint.route('/student/api/institutional-history')
def student_history_data():
    if session.get('user_role') != 'student' or not session.get('is_authenticated') or not session.get('student_id'):
        return jsonify({'error': 'No autorizado'}), 403
    if request.args.get('student_id') not in (None, str(session['student_id'])):
        return jsonify({'error': 'Solo puedes consultar tu propio historial.'}), 403
    records = fetch_history(student_id=session['student_id'])
    # The student can see grades, not provenance hashes or import identities.
    return jsonify({'success': True, 'records': [
        {key: row[key] for key in ('academic_year', 'period', 'ratings', 'final_rating')}
        for row in records
    ]})
