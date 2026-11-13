import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from services import db_service, mock_data
from services.ml.model_registry import get_model_registry
from services.student_learning_service import get_student_risk_feedback, build_student_risk_payload


class TestStudentRiskPrediction(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True
        db_service._use_mock = lambda: True

    def test_authenticated_student_can_view_own_prediction(self):
        """1. Alumno autenticado puede ver su predicción exitosamente."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'alumno1'
            sess['user_role'] = 'student'
            sess['student_id'] = 1
            sess['student_name'] = 'Juan Pérez'
            sess['user_grade'] = 5
            sess['is_authenticated'] = True

        response = self.client.get('/student/api/risk-prediction')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('risk_level', data)
        self.assertIn(data['risk_level'], ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'])
        self.assertIn('probability', data)
        self.assertIn('factors', data)
        self.assertIsInstance(data['factors'], list)
        self.assertIn('motivational_message', data)
        self.assertTrue(len(data['motivational_message']) > 0)
        self.assertIn('recommendations', data)
        self.assertIsInstance(data['recommendations'], list)

    def test_unauthenticated_request_is_rejected(self):
        """Petición sin sesión debe retornar 401."""
        response = self.client.get('/student/api/risk-prediction')
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data.get('success', True))

    def test_student_cannot_view_prediction_of_another_student(self):
        """2. Alumno no puede ver la predicción de otro estudiante (rechazo IDOR con 403)."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'alumno1'
            sess['user_role'] = 'student'
            sess['student_id'] = 1
            sess['student_name'] = 'Juan Pérez'
            sess['user_grade'] = 5
            sess['is_authenticated'] = True

        # Intento de solicitar la predicción del estudiante 2
        response = self.client.get('/student/api/risk-prediction?student_id=2')
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data.get('success'))
        self.assertEqual(data.get('code'), 'FORBIDDEN')
        self.assertIn('No autorizado', data.get('error', ''))

    def test_teacher_or_other_role_cannot_access_student_prediction_endpoint(self):
        """Docente u otro rol no puede consultar el endpoint exclusivo de estudiantes."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'profesor1'
            sess['user_role'] = 'teacher'
            sess['student_id'] = None
            sess['is_authenticated'] = True

        response = self.client.get('/student/api/risk-prediction')
        # _auth_check() redirige o rechaza con 401
        self.assertIn(response.status_code, [401, 302])

    def test_model_not_available_returns_clear_message(self):
        """3. Si el modelo no está disponible -> mensaje claro y código MODEL_NOT_AVAILABLE."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'alumno1'
            sess['user_role'] = 'student'
            sess['student_id'] = 1
            sess['student_name'] = 'Juan Pérez'
            sess['user_grade'] = 5
            sess['is_authenticated'] = True

        registry = get_model_registry()
        with patch.object(registry, 'is_available', return_value=False):
            response = self.client.get('/student/api/risk-prediction')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertFalse(data['success'])
            self.assertEqual(data['code'], 'MODEL_NOT_AVAILABLE')
            self.assertIn('no está disponible', data['message'].lower())
            self.assertEqual(data['risk_level'], 'UNKNOWN')

    def test_response_contains_explanatory_factors(self):
        """4. La respuesta contiene factores explicativos interpretables para el alumno."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'alumno1'
            sess['user_role'] = 'student'
            sess['student_id'] = 1
            sess['student_name'] = 'Juan Pérez'
            sess['user_grade'] = 5
            sess['is_authenticated'] = True

        response = self.client.get('/student/api/risk-prediction')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(len(data['factors']) > 0)
        # Ningún factor debe contener código o IDs crudos de base de datos
        for factor in data['factors']:
            self.assertIsInstance(factor, str)
            self.assertNotIn('ALU-', factor)

    def test_motivational_messages_by_risk_level(self):
        """Verificación exacta de los mensajes motivacionales requeridos por nivel de riesgo."""
        high_feedback = get_student_risk_feedback('HIGH')
        self.assertEqual(
            high_feedback['motivational_message'],
            "💪 No te rindas. Todavía puedes mejorar. Practica un poco cada día."
        )
        self.assertEqual(high_feedback['academic_status'], "⚠ Necesitas reforzar algunos temas")

        medium_feedback = get_student_risk_feedback('MEDIUM')
        self.assertEqual(
            medium_feedback['motivational_message'],
            "🚀 Vas avanzando. Continúa practicando para mejorar."
        )

        low_feedback = get_student_risk_feedback('LOW')
        self.assertEqual(
            low_feedback['motivational_message'],
            "⭐ Excelente trabajo. Sigue manteniendo tu esfuerzo."
        )

    def test_student_dashboard_html_renders_risk_card(self):
        """La vista HTML del dashboard del alumno incluye la tarjeta de predicción personalizada."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'alumno1'
            sess['user_role'] = 'student'
            sess['student_id'] = 1
            sess['student_name'] = 'Juan Pérez'
            sess['user_grade'] = 5
            sess['is_authenticated'] = True

        response = self.client.get('/student/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('student-risk-card', html)
        self.assertIn('Mi Estado Académico y Recomendaciones IA', html)
        self.assertIn('Juan Pérez', html)


if __name__ == '__main__':
    unittest.main()
