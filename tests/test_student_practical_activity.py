from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import app


def _student_session(client):
    with client.session_transaction() as session:
        session['user'] = 'alumno'
        session['user_role'] = 'student'
        session['student_id'] = 7
        session['user_grade'] = 5
        session['user_section'] = 'A'
        session['is_authenticated'] = True


def test_student_can_read_own_submission_review():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        _student_session(test_client)
        submission = {
            'id': 31,
            'student_id': 7,
            'topic_id': 4,
            'title': 'Mi presentación',
            'file_name': 'trabajo.pdf',
            'status': 'revisado',
            'teacher_score': 18,
            'teacher_feedback': 'Buen trabajo',
            'submitted_at': '2026-10-01',
            'reviewed_at': '2026-10-02',
        }
        with patch('controllers.student_controller._published_topic_for_student', return_value={'id': 4}), \
             patch('controllers.student_controller.fetch_submissions', return_value=[submission]) as fetch_mock:
            response = test_client.get('/student/api/topics/4/submissions')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['submissions'][0]['teacher_score'] == 18
    assert payload['submissions'][0]['teacher_feedback'] == 'Buen trabajo'
    fetch_mock.assert_called_once_with(student_id=7, topic_id=4)


def test_student_submission_upload_creates_reviewable_submission():
    app.config['TESTING'] = True
    original_dir = app.config.get('STUDENT_SUBMISSION_DIR')
    try:
        with TemporaryDirectory() as upload_dir, app.test_client() as client:
            _student_session(client)
            app.config['STUDENT_SUBMISSION_DIR'] = upload_dir
            with patch('controllers.student_controller._published_topic_for_student', return_value={'id': 4}), \
                 patch('controllers.student_controller.create_student_submission', return_value=32) as create_mock:
                response = client.post(
                    '/student/api/topics/4/submission',
                    data={'title': 'Mi trabajo', 'file': (BytesIO(b'contenido'), 'trabajo.pdf')},
                    content_type='multipart/form-data',
                )

            assert response.status_code == 201
            assert response.get_json()['submission_id'] == 32
            create_args = create_mock.call_args.args
            assert create_args[0:3] == (7, 4, 'Mi trabajo')
            assert Path(create_args[3].replace('/static/uploads/student_work/', upload_dir + '/')).is_file()
            assert create_args[4] == 'trabajo.pdf'
    finally:
        if original_dir is None:
            app.config.pop('STUDENT_SUBMISSION_DIR', None)
        else:
            app.config['STUDENT_SUBMISSION_DIR'] = original_dir


def test_student_submission_rejects_executable_files():
    app.config['TESTING'] = True
    with app.test_client() as client:
        _student_session(client)
        with patch('controllers.student_controller._published_topic_for_student', return_value={'id': 4}):
            response = client.post(
                '/student/api/topics/4/submission',
                data={'file': (BytesIO(b'not safe'), 'program.exe')},
                content_type='multipart/form-data',
            )

    assert response.status_code == 400
    assert 'Formato no permitido' in response.get_json()['error']


def test_student_cannot_mark_unpublished_or_unassigned_material_as_read():
    app.config['TESTING'] = True
    with app.test_client() as client:
        _student_session(client)
        with patch('controllers.student_controller.fetch_material_by_id', return_value={
            'id': 99, 'topic_id': 44, 'status': 'PUBLISHED'
        }), patch('controllers.student_controller._published_topic_for_student', return_value=None), \
             patch('controllers.student_controller.mark_material_reviewed') as mark_mock:
            response = client.post('/student/api/materials/99/reviewed')

    assert response.status_code == 404
    mark_mock.assert_not_called()


def test_student_read_state_uses_presentation_review_tracking():
    app.config['TESTING'] = True
    with app.test_client() as client:
        _student_session(client)
        presentation = {
            'id': 21,
            'topic_id': 4,
            'status': 'PUBLISHED',
        }
        with patch('controllers.student_controller.fetch_presentation_by_id', return_value=presentation), \
             patch('controllers.student_controller._published_topic_for_student', return_value={'id': 4}), \
             patch('controllers.student_controller.mark_material_reviewed', return_value=True) as mark_mock:
            response = client.post('/student/api/materials/21/reviewed?source=presentation')

    assert response.status_code == 200
    mark_mock.assert_called_once_with(21, 7, source='presentation')


def test_practical_activity_returns_materials_and_reviewed_submissions_together():
    app.config['TESTING'] = True
    with app.test_client() as client:
        _student_session(client)
        submissions = [{
            'id': 32,
            'title': 'Mi trabajo',
            'file_name': 'trabajo.pdf',
            'status': 'revisado',
            'teacher_score': 19,
            'teacher_feedback': 'Excelente',
            'submitted_at': '2026-10-01',
            'reviewed_at': '2026-10-02',
        }]
        with patch('controllers.student_controller._published_topic_for_student', return_value={'id': 4}), \
             patch('controllers.student_controller.fetch_learning_materials', return_value=[{'id': 5, 'title': 'Guía'}]) as materials_mock, \
             patch('controllers.student_controller.fetch_submissions', return_value=submissions) as submissions_mock:
            response = client.get('/student/api/topics/4/practical-activity')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['materials'] == [{'id': 5, 'title': 'Guía'}]
    assert payload['submissions'][0]['teacher_score'] == 19
    materials_mock.assert_called_once_with(4, 7)
    submissions_mock.assert_called_once_with(student_id=7, topic_id=4)
