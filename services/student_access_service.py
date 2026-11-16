"""Shared grade and section authorization for student learning resources."""
from flask import g, session
from services import db_service


def current_student_section():
    if 'student_profile' not in g:
        g.student_profile = db_service.fetch_student_by_id(session.get('student_id', 0)) or {}
    return str(g.student_profile.get('section') or session.get('user_section') or '').strip().upper()


def topic_for_student(topic_id, require_published=True):
    topic = db_service.fetch_topic_by_id(topic_id)
    if not topic or int(topic.get('grade') or 0) != int(session.get('user_grade') or 5):
        return None
    section = str(topic.get('section') or '').strip().upper()
    if section and section != current_student_section():
        return None
    if require_published and str(topic.get('status') or '').strip() != 'Publicado':
        return None
    return topic
