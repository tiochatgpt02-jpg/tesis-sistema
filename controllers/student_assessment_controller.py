from datetime import datetime, timezone
import uuid
from flask import Blueprint, jsonify, request, session
from services import db_service
from services.student_access_service import topic_for_student
from services.learning_attempt_service import start_attempt, submit_attempt, public_attempt, AttemptError

student_assessment_blueprint = Blueprint('student_assessments', __name__, url_prefix='/student')


def _denied():
    if not session.get('is_authenticated') or session.get('user_role') != 'student' or not session.get('student_id'):
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    return None


def _assessment(identity, published=True):
    assessment = db_service.fetch_assessment_by_id(identity)
    if not assessment or not topic_for_student(assessment['topic_id'], require_published=published):
        return None
    if published and assessment.get('status') != 'PUBLISHED':
        return None
    return assessment


@student_assessment_blueprint.route('/api/topics/<int:topic_id>/assessments')
def list_published_assessments(topic_id):
    denied = _denied()
    if denied:
        return denied
    if not topic_for_student(topic_id):
        return jsonify({'success': False, 'error': 'Clase no disponible.'}), 404
    assessments = db_service.fetch_assessments_for_topic(topic_id, status='PUBLISHED')
    return jsonify({'success': True, 'assessments': [
        {'id': row['id'], 'title': row['title'], 'kind': row.get('kind', 'exam'),
         'total_questions': row.get('approved_questions', 0)}
        for row in assessments if row.get('approved_questions', 0)
    ]})


@student_assessment_blueprint.route('/api/assessments/<int:assessment_id>', methods=['GET'])
def preview_assessment(assessment_id):
    denied = _denied()
    if denied:
        return denied
    assessment = _assessment(assessment_id)
    if not assessment:
        return jsonify({'success': False, 'error': 'Evaluación no disponible.'}), 404
    kind = assessment.get('kind', 'exam')
    return jsonify({'success': True, 'assessment': {'id': assessment_id, 'title': assessment['title'], 'kind': kind,
                    'question_count': sum(bool(question.get('approved')) for question in assessment['questions']),
                    'duration_minutes': 30 if kind == 'exam' else None,
                    'rule': 'Un intento; el docente puede autorizar otro.' if kind == 'exam' else 'Puedes volver a practicar; se toma tu último intento.'}})


@student_assessment_blueprint.route('/api/assessments/<int:assessment_id>/start', methods=['POST'])
def begin_assessment(assessment_id):
    denied = _denied()
    if denied:
        return denied
    assessment = _assessment(assessment_id)
    if not assessment:
        return jsonify({'success': False, 'error': 'Evaluación no disponible.'}), 404
    questions = [question for question in assessment['questions'] if question.get('approved')]
    if not questions:
        return jsonify({'success': False, 'error': 'El docente todavía no ha aprobado las preguntas.'}), 409
    kind = assessment.get('kind', 'exam')
    try:
        attempt = start_attempt(session['student_id'], assessment['topic_id'], kind, str(assessment_id), questions, assessment_id)
    except AttemptError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 409
    elapsed = max(0, (datetime.now(timezone.utc) - attempt['started_at']).total_seconds())
    return jsonify({'success': True, 'assessment_id': assessment_id, 'title': assessment['title'], 'kind': kind,
                    'student_id': session['student_id'], 'attempt': public_attempt(attempt),
                    'remaining_seconds': max(0, int(1800-elapsed)) if kind == 'exam' else None})


@student_assessment_blueprint.route('/api/assessments/<int:assessment_id>/attempt', methods=['POST'])
def finish_assessment(assessment_id):
    denied = _denied()
    if denied:
        return denied
    # Previously issued attempts retain their frozen version even if editing has
    # temporarily returned the assessment to review. New starts remain blocked.
    assessment = _assessment(assessment_id, published=False)
    if not assessment:
        return jsonify({'success': False, 'error': 'Evaluación no disponible.'}), 404
    data = request.get_json(silent=True) or {}
    try:
        uuid.UUID(str(data.get('attempt_id', '')))
        result = submit_attempt(data['attempt_id'], session['student_id'], assessment.get('kind', 'exam'),
                                str(assessment_id), data.get('answers', {}))
    except (ValueError, AttemptError) as exc:
        return jsonify({'success': False, 'error': str(exc)}), 409
    return jsonify({'success': True, 'result': result})
