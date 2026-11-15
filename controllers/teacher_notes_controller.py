from services.grading_policy_service import get_policy
from services.bimester_grade_service import with_component_results, current_term
from flask import Blueprint, jsonify, request, session

from services.db_service import fetch_student_results, fetch_students
from services.teacher_note_service import build_gradebook_summary

teacher_notes_blueprint = Blueprint('teacher_notes', __name__, url_prefix='/teacher')


@teacher_notes_blueprint.route('/api/notes/summary', methods=['POST'])
def api_notes_summary():
    if session.get('user_role') != 'teacher':
        return jsonify({'error': 'No autorizado'}), 401
    payload = request.get_json() or {}
    results = fetch_student_results(
        student_id=payload.get('student_id'),
        activity_type=payload.get('activity_type'),
        date_from=payload.get('date_from'),
        date_to=payload.get('date_to'),
    )
    policy = get_policy()
    year, period = current_term()
    students = fetch_students()
    if payload.get('student_id'):
        students = [row for row in students if int(row['id']) == int(payload['student_id'])]
    results = with_component_results(students, results, policy, int(payload.get('period') or period), int(payload.get('year') or year))
    return jsonify({**build_gradebook_summary(results, policy), 'results': results})
