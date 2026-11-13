import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from services.presentation_storage import resolve_presentation_path


class TeacherPresentationScopeTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['user'] = {'id': 1, 'username': 'profesor'}
            session['is_authenticated'] = True
            session['user_role'] = 'teacher'
            session['user_id'] = 1
            session['teacher_name'] = 'Profesor'

    def test_upload_creates_grade_session_topic_and_keeps_session_scope(self):
        with patch('controllers.teacher_controller.fetch_all_topics', return_value=[{'id': 5, 'title': 'Sesión 5', 'grade': 5, 'status': 'Publicado'}]), \
             patch('controllers.teacher_controller.insert_topic', return_value=999) as insert_topic_mock, \
             patch('controllers.teacher_controller.fetch_presentation_by_topic_session', return_value=None), \
        patch('controllers.teacher_controller.fetch_assessments_for_topic', return_value=[]), \
        patch('controllers.teacher_controller.insert_presentation', return_value=123) as insert_presentation_mock, \
             patch('controllers.teacher_controller.save_presentation_file', return_value=('presentations/demo.pdf', 8)):
            response = self.client.post(
                '/teacher/api/upload-presentation',
                data={
                    'grade': '5',
                    'unit': '2',
                    'section': 'B',
                    'session_number': '7',
                    'title': 'Sesión 7',
                    'description': 'Observa la presentación y resuelve la actividad.',
                    'file': (io.BytesIO(b'%PDF-1.4\n'), 'demo.pdf'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(insert_topic_mock.called)
        self.assertEqual(insert_topic_mock.call_args[0][0], 'Sesión 7')
        self.assertEqual(insert_topic_mock.call_args[0][2], 5)
        self.assertEqual(insert_topic_mock.call_args[0][3:], ('Pendiente', 'B', 2, 7))
        self.assertEqual(insert_presentation_mock.call_args[0][0], 999)
        self.assertEqual(insert_presentation_mock.call_args[0][2], 7)
        self.assertEqual(insert_presentation_mock.call_args[0][3], 'Observa la presentación y resuelve la actividad.')
        self.assertEqual(insert_presentation_mock.call_args[0][8], 'DRAFT')

    def test_upload_from_topic_card_keeps_selected_topic_and_session(self):
        topic = {
            'id': 987,
            'title': 'Sesión 7',
            'grade': 5,
            'section': 'B',
            'session_number': 7,
        }
        with patch('controllers.teacher_controller.fetch_all_topics', return_value=[topic]), \
             patch('controllers.teacher_controller.insert_topic') as insert_topic_mock, \
             patch('controllers.teacher_controller.fetch_presentation_by_topic_session', return_value=None), \
             patch('controllers.teacher_controller.fetch_assessments_for_topic', return_value=[]), \
             patch('controllers.teacher_controller.insert_presentation', return_value=123) as insert_presentation_mock, \
             patch('controllers.teacher_controller.save_presentation_file', return_value=('presentations/demo.pptx', 8)):
            response = self.client.post(
                '/teacher/api/upload-presentation',
                data={
                    'topic_id': '987',
                    'grade': '5',
                    'section': 'B',
                    'session_number': '7',
                    'title': 'Material - Sesión 7',
                    'file': (io.BytesIO(b'pptx'), 'demo.pptx'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['topic_id'], 987)
        self.assertEqual(response.json['session_number'], 7)
        insert_topic_mock.assert_not_called()
        self.assertEqual(insert_presentation_mock.call_args.args[0], 987)

    def test_upload_can_publish_material_and_description_for_students_immediately(self):
        topic = {
            'id': 987,
            'title': 'Sesión 7',
            'grade': 5,
            'section': 'B',
            'session_number': 7,
        }
        with patch('controllers.teacher_controller.fetch_all_topics', return_value=[topic]), \
             patch('controllers.teacher_controller.fetch_presentation_by_topic_session', return_value=None), \
             patch('controllers.teacher_controller.fetch_assessments_for_topic', return_value=[]), \
             patch('controllers.teacher_controller.insert_presentation', return_value=123) as insert_presentation_mock, \
             patch('controllers.teacher_controller.save_presentation_file', return_value=('presentations/demo.pdf', 8)):
            response = self.client.post(
                '/teacher/api/upload-presentation',
                data={
                    'topic_id': '987',
                    'grade': '5',
                    'session_number': '7',
                    'title': 'Material de la sesión',
                    'description': 'Lee esta indicación antes de resolver la actividad.',
                    'publish_to_students': 'true',
                    'file': (io.BytesIO(b'%PDF-1.4\n'), 'demo.pdf'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'PUBLISHED')
        self.assertEqual(insert_presentation_mock.call_args.args[3], 'Lee esta indicación antes de resolver la actividad.')
        self.assertEqual(insert_presentation_mock.call_args.args[8], 'PUBLISHED')

    def test_replacing_presentation_keeps_selected_publication_status(self):
        topic = {
            'id': 987,
            'title': 'Sesión 7',
            'grade': 5,
            'section': 'B',
            'session_number': 7,
        }
        existing = {'id': 123, 'file_path': 'presentations/old.pdf'}
        with patch('controllers.teacher_controller.fetch_all_topics', return_value=[topic]), \
             patch('controllers.teacher_controller.fetch_presentation_by_topic_session', return_value=existing), \
             patch('controllers.teacher_controller.fetch_assessments_for_topic', return_value=[{'id': 44}]), \
             patch('controllers.teacher_controller.update_assessment_status') as update_assessment_status_mock, \
             patch('controllers.teacher_controller.delete_stored_presentation_file'), \
             patch('controllers.teacher_controller.update_presentation') as update_presentation_mock, \
             patch('controllers.teacher_controller.save_presentation_file', return_value=('presentations/demo.pdf', 8)):
            response = self.client.post(
                '/teacher/api/upload-presentation',
                data={
                    'topic_id': '987',
                    'grade': '5',
                    'session_number': '7',
                    'title': 'Material actualizado',
                    'description': 'Descripción actualizada para los alumnos.',
                    'publish_to_students': 'true',
                    'file': (io.BytesIO(b'%PDF-1.4\n'), 'demo.pdf'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['status'], 'PUBLISHED')
        self.assertTrue(response.json['replaced'])
        self.assertEqual(response.json['invalidated_assessments'], 1)
        self.assertEqual(update_presentation_mock.call_args.args[6], 'PUBLISHED')
        update_assessment_status_mock.assert_called_once_with(44, 'PENDING_REVIEW')

    def test_private_presentation_storage_resolves_inside_presentations_directory(self):
        with app.app_context():
            resolved_path = resolve_presentation_path('presentations/demo.pptx')

        expected_path = Path(app.instance_path) / 'uploads' / 'presentations' / 'demo.pptx'
        self.assertEqual(resolved_path, expected_path.resolve())

    def test_teacher_can_publish_presentation(self):
        with patch(
            'controllers.teacher_controller.fetch_presentation_by_id',
            return_value={'id': 123, 'topic_id': 999, 'status': 'DRAFT'},
        ), patch('controllers.teacher_controller.update_presentation_status') as update_status:
            response = self.client.post('/teacher/api/presentations/123/publish')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'PUBLISHED')
        update_status.assert_called_once_with(123, 'PUBLISHED')

    def test_student_cannot_download_draft_presentation(self):
        with self.client.session_transaction() as session:
            session['user_role'] = 'student'
            session['student_id'] = 2
            session['user_grade'] = 5

        with patch(
            'controllers.student_controller.fetch_presentation_by_id',
            return_value={'id': 123, 'topic_id': 999, 'status': 'DRAFT'},
        ):
            response = self.client.get('/student/api/presentations/123/file')

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_access_presentation_for_another_section(self):
        with self.client.session_transaction() as session:
            session['user_role'] = 'student'
            session['student_id'] = 2
            session['user_grade'] = 5

        with patch(
            'controllers.student_controller.fetch_presentation_by_id',
            return_value={'id': 123, 'topic_id': 999, 'status': 'PUBLISHED'},
        ), patch(
            'controllers.student_controller.fetch_topic_by_id',
            return_value={'id': 999, 'grade': 5, 'section': 'B', 'status': 'Publicado'},
        ), patch(
            'controllers.student_controller.fetch_student_by_id',
            return_value={'id': 2, 'grade': 5, 'section': 'A'},
        ):
            response = self.client.get('/student/api/presentations/123/file')

        self.assertEqual(response.status_code, 404)

    def test_teacher_assessment_and_game_lists_accept_academic_filters(self):
        with patch(
            'controllers.teacher_assessment_controller.fetch_all_assessments',
            return_value=[],
        ) as assessments_mock, patch(
            'controllers.teacher_ai_games_controller.fetch_ai_generated_games',
            return_value=[],
        ) as games_mock:
            assessment_response = self.client.get(
                '/teacher/api/assessments?grade=5&section=B&unit=2&session_number=7'
            )
            games_response = self.client.get(
                '/teacher/api/ai-games?grade=5&section=B&unit=2&session_number=7'
            )

        self.assertEqual(assessment_response.status_code, 200)
        self.assertEqual(games_response.status_code, 200)
        assessments_mock.assert_called_once_with(
            status=None,
            grade=5,
            section='B',
            unit_number=2,
            session_number=7,
        )
        games_mock.assert_called_once_with(
            topic_id=None,
            status=None,
            presentation_id=None,
            material_id=None,
            grade=5,
            section='B',
            unit_number=2,
            session_number=7,
        )

    def test_assessment_generation_accepts_questions_verified_from_short_presentation(self):
        questions = [
            {
                'question': f'Pregunta basada en el PPT {index}?',
                'options': [f'Respuesta {index}', 'Alternativa B', 'Alternativa C'],
                'answer': f'Respuesta {index}',
            }
            for index in range(1, 5)
        ]
        with patch(
            'controllers.teacher_assessment_controller.fetch_topic_by_id',
            return_value={'id': 16, 'title': 'Sesión 1', 'grade': 5},
        ), patch(
            'controllers.teacher_assessment_controller.get_presentations_for_topic',
            return_value=[{'id': 4, 'topic_id': 16, 'session_number': 1}],
        ), patch(
            'controllers.teacher_assessment_controller.MaterialExtractorService.extract_from_presentation_record',
            return_value={'raw_text': 'Contenido educativo del PPT', 'title': 'Material'},
        ), patch(
            'controllers.teacher_assessment_controller.generate_questions_from_teacher_material',
            return_value={'success': True, 'source': 'fallback', 'questions': questions},
        ) as generate_questions, patch(
            'controllers.teacher_assessment_controller.create_assessment',
            return_value=321,
        ), patch(
            'controllers.teacher_assessment_controller.update_assessment_status',
        ), patch(
            'controllers.teacher_assessment_controller.create_question',
            side_effect=range(1, 5),
        ):
            response = self.client.post(
                '/teacher/api/assessments/generate',
                json={'topic_id': 16, 'title': 'Evaluación - Sesión 1'},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json['questions']), 4)
        self.assertIn('4 preguntas verificables', response.json['message'])
        generate_questions.assert_called_once()
        self.assertEqual(generate_questions.call_args.kwargs['timeout'], 45)

    def test_assessment_generation_reports_when_presentation_has_no_verifiable_questions(self):
        with patch(
            'controllers.teacher_assessment_controller.fetch_topic_by_id',
            return_value={'id': 16, 'title': 'Sesión 1', 'grade': 5},
        ), patch(
            'controllers.teacher_assessment_controller.get_presentations_for_topic',
            return_value=[{'id': 4, 'topic_id': 16, 'session_number': 1}],
        ), patch(
            'controllers.teacher_assessment_controller.MaterialExtractorService.extract_from_presentation_record',
            return_value={'raw_text': 'Contenido educativo del PPT', 'title': 'Material'},
        ), patch(
            'controllers.teacher_assessment_controller.generate_questions_from_teacher_material',
            return_value={'success': True, 'questions': []},
        ), patch(
            'controllers.teacher_assessment_controller.create_assessment',
        ) as create_assessment:
            response = self.client.post(
                '/teacher/api/assessments/generate',
                json={'topic_id': 16},
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn('No se pudieron verificar preguntas', response.json['error'])
        create_assessment.assert_not_called()


if __name__ == '__main__':
    unittest.main()
