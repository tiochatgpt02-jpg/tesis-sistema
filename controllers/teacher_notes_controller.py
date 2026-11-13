from services.grading_policy_service import get_policy
from flask import Blueprint, jsonify, request, session

from services.db_service import fetch_student_results
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
    return jsonify({**build_gradebook_summary(results, get_policy()), 'results': results})
