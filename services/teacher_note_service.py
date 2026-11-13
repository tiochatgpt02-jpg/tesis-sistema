from __future__ import annotations

from services.grading_policy_service import academic_notes, academic_average

from typing import Any, Dict, List


def build_gradebook_summary(results: List[Dict[str, Any]], policy=None) -> Dict[str, Any]:
    students: List[Dict[str, Any]] = []
    by_student: Dict[str, Dict[str, Any]] = {}
    all_scores: List[float] = []

    for item in academic_notes(results):
        if item.get('activity_type') == 'juegos':
            continue
        student_id = item.get('student_id')
        student_name = item.get('student_name') or f'Estudiante {student_id}'
        score = float(item.get('score', 0) or 0)
        activity_type = item.get('activity_type', 'actividades')
        topic = item.get('topic', 'General')
        key = str(student_id)

        if key not in by_student:
            by_student[key] = {
                'student_id': student_id,
                'student_name': student_name,
                'scores': [],
                'notes': [],
                'activities': [],
                'topics': set(),
            }

        by_student[key]['scores'].append(score)
        by_student[key]['notes'].append(item)
        by_student[key]['activities'].append(activity_type)
        by_student[key]['topics'].add(topic)
        all_scores.append(score)

    for student in by_student.values():
        students.append({
            'student_id': student['student_id'],
            'student_name': student['student_name'],
            'average_score': academic_average(student['notes'], policy),
            'activities': student['activities'],
            'topics': sorted(student['topics']),
        })

    students.sort(key=lambda x: x['average_score'] if x['average_score'] is not None else -1, reverse=True)
    valid = [s['average_score'] for s in students if s['average_score'] is not None]
    overview = {
        'policy': policy,
        'average_status': 'weighted' if policy else 'provisional',
        'average_score': round(sum(valid) / len(valid), 2) if valid else None,
        'students_count': len(students),
        'top_student': students[0]['student_name'] if students else 'Sin estudiantes',
    }
    return {'students': students, 'overview': overview}
