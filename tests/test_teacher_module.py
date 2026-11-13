import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.teacher_service import build_evaluation_questions, build_teacher_dashboard_summary, build_topic_generation_payload


class TeacherModuleServiceTests(unittest.TestCase):
    def test_build_topic_generation_payload_includes_required_sections(self):
        payload = build_topic_generation_payload('Word', 6)
        self.assertEqual(payload['title'], 'Word')
        self.assertIn('explanation', payload)
        self.assertIn('examples', payload)
        self.assertIn('activities', payload)
        self.assertIn('evaluation_questions', payload)
        self.assertIn('game', payload)
        self.assertEqual(payload['grade'], 6)

    def test_build_teacher_dashboard_summary_returns_expected_metrics(self):
        summary = build_teacher_dashboard_summary(
            students=[
                {'grade': 4, 'progress': 60},
                {'grade': 5, 'progress': 70},
                {'grade': 6, 'progress': 80},
            ],
            topics=[
                {'grade': 4, 'status': 'Completado'},
                {'grade': 5, 'status': 'En proceso'},
                {'grade': 6, 'status': 'Pendiente'},
            ],
            activities_count=12,
            evaluations_count=7,
        )
        self.assertEqual(summary['total_students'], 3)
        self.assertEqual(summary['average_progress'], 70)
        self.assertEqual(summary['activities_count'], 12)
        self.assertEqual(summary['evaluations_count'], 7)
        self.assertIn('students_by_grade', summary)

    def test_evaluation_questions_are_unique_and_topic_specific(self):
        questions = build_evaluation_questions('Paint', 4)
        texts = [item['question'] for item in questions]
        self.assertEqual(len(questions), 10)
        self.assertEqual(len(texts), len(set(texts)))
        self.assertTrue(all('Paint' in item['question'] for item in questions))
        self.assertTrue(all(item['answer'] in item['options'] for item in questions))


if __name__ == '__main__':
    unittest.main()
