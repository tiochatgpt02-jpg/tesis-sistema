import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.teacher_assessment_service import generate_assessment, grade_assessment
from services.teacher_note_service import build_gradebook_summary


def test_generate_assessment_returns_required_fields():
    assessment = generate_assessment('Word', 5, 3, 'media')
    assert assessment['grade'] == 5
    assert assessment['topic'] == 'Word'
    assert len(assessment['questions']) == 3
    assert 'answer' in assessment['questions'][0]


def test_grade_assessment_calculates_score_and_percent():
    result = grade_assessment([
        {'correct': True, 'points': 10},
        {'correct': False, 'points': 10},
        {'correct': True, 'points': 10},
    ])
    assert result['score'] == 20
    assert result['percentage'] == 66.67
    assert result['correct_answers'] == 2


def test_build_gradebook_summary_groups_by_student():
    summary = build_gradebook_summary([
        {'student_id': 1, 'student_name': 'Ana', 'score': 18, 'activity_type': 'evaluaciones', 'topic': 'Word'},
        {'student_id': 1, 'student_name': 'Ana', 'score': 12, 'activity_type': 'juegos', 'topic': 'Word'},
        {'student_id': 2, 'student_name': 'Luis', 'score': 9, 'activity_type': 'actividades', 'topic': 'Excel'},
    ])
    assert summary['students'][0]['student_name'] == 'Ana'
    assert summary['overview']['average_score'] == 13.5
    assert summary['students'][0]['average_score'] == 18
