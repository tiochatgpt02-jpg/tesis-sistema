from services import db_service
from services.student_learning_service import build_student_progress


def test_topic_progress_uses_required_activity_completion_not_scores(monkeypatch):
    from services import mock_data

    monkeypatch.setattr(db_service, '_use_mock', lambda: True)
    monkeypatch.setattr(mock_data, 'MOCK_STUDENT_NOTES', [
        {
            'student_id': 1,
            'topic_id': 501,
            'activity_type': 'actividades',
            'score': 20,
            'percentage': 100,
        },
        {
            'student_id': 1,
            'topic_id': 502,
            'activity_type': 'actividades',
            'score': 0,
            'percentage': 0,
        },
        {
            'student_id': 1,
            'topic_id': 502,
            'activity_type': 'evaluaciones',
            'score': 0,
            'percentage': 0,
        },
        {
            'student_id': 1,
            'topic_id': 502,
            'activity_type': 'juegos',
            'score': 0,
            'percentage': 0,
        },
    ])
    monkeypatch.setattr(mock_data, 'MOCK_TOPICS', {
        5: [
            {'id': 501, 'title': 'Tema con una actividad'},
            {'id': 502, 'title': 'Tema con las tres actividades'},
        ],
    })
    monkeypatch.setattr(
        db_service,
        'fetch_student_progress',
        lambda student_id: {'overall_progress': 100, 'completed_topics': 1, 'study_time': '0h', 'average_grade': 20},
    )
    monkeypatch.setattr(db_service, 'fetch_student_activity_summary', lambda student_id: {})

    progress = build_student_progress(1, [
        {'id': 501, 'title': 'Tema con una actividad'},
        {'id': 502, 'title': 'Tema con las tres actividades'},
    ])
    topics = {item['id']: item for item in progress['topics']}

    assert topics[501]['score'] == 10.0
    assert topics[501]['completed_activities'] == 1
    assert topics[501]['completed'] is False
    assert topics[502]['score'] == 20.0
    assert topics[502]['completed_activities'] == 2
    assert topics[502]['completed'] is True
    assert progress['completed'] == 1
    assert progress['overall'] == 15.0

    one_topic_progress = build_student_progress(1, [
        {'id': 502, 'title': 'Tema con las tres actividades'},
    ])
    assert one_topic_progress['overall'] == 20.0
