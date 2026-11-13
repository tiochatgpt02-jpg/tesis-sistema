import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


class TeacherSubmissionReviewTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['user'] = {'id': 1, 'username': 'profesor'}
            session['is_authenticated'] = True
            session['user_role'] = 'teacher'
            session['user_id'] = 1
            session['teacher_name'] = 'Profesor'

    def test_review_submission_updates_student_notes_for_gradebook(self):
        mock_submission = {
            'id': 12,
            'student_id': 7,
            'topic_id': 3,
            'status': 'pendiente',
            'teacher_score': None,
            'teacher_feedback': '',
        }

        with patch('controllers.teacher_controller.fetch_submissions', return_value=[mock_submission]), \
             patch('controllers.teacher_controller.review_student_submission', return_value=True) as review_mock, \
             patch('controllers.teacher_controller.record_student_result', return_value=True) as record_mock:
            response = self.client.put(
                '/teacher/api/submissions/12/review',
                json={'score': 17.6, 'feedback': 'Muy bien'}
            )

        self.assertEqual(response.status_code, 200)
        review_mock.assert_called_once_with(12, 17.6, 'Muy bien')
        record_mock.assert_called_once_with(7, 3, 'actividades', 'submission:12', 17.6, correct_answers=0, wrong_answers=0, time_spent_seconds=0, percentage=88)

    def test_manual_review_without_submission_records_student_note(self):
        with patch('controllers.teacher_controller.record_student_result', return_value=True) as record_mock:
            response = self.client.put(
                '/teacher/api/submissions/review',
                json={'student_id': 9, 'score': 0, 'feedback': 'Sin entrega; reprobado por inasistencia'}
            )

        self.assertEqual(response.status_code, 200)
        record_mock.assert_called_once_with(9, None, 'actividades', 'entrega_revisada', 0, correct_answers=0, wrong_answers=0, time_spent_seconds=0, percentage=0)


if __name__ == '__main__':
    unittest.main()
