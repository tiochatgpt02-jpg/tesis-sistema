from __future__ import annotations

from datetime import date
from services.grading_policy_service import academic_notes, academic_average, component_summary
from typing import Any, Dict, List, Optional, Tuple


PERIODS = {
    '1': {'label': 'Bimestre 1', 'start': (3, 1), 'end': (5, 31)},
    '2': {'label': 'Bimestre 2', 'start': (6, 1), 'end': (7, 31)},
    '3': {'label': 'Bimestre 3', 'start': (8, 1), 'end': (10, 31)},
    '4': {'label': 'Bimestre 4', 'start': (11, 1), 'end': (12, 31)},
}

GRADE_LABELS = {
    4: '4to Primaria',
    5: '5to Primaria',
    6: '6to Primaria',
}


def achievement_level(score_20: float) -> Dict[str, str]:
    if score_20 >= 18:
        return {'code': 'AD', 'label': 'Logro destacado'}
    if score_20 >= 14:
        return {'code': 'A', 'label': 'Logro esperado'}
    if score_20 >= 11:
        return {'code': 'B', 'label': 'En proceso'}
    return {'code': 'C', 'label': 'Necesita apoyo'}


def to_scale_20(score: Any) -> float:
    try:
        value = float(score or 0)
    except (TypeError, ValueError):
        return 0.0
    if value > 20:
        return round(min(20, value / 5 if value <= 100 else 20), 2)
    return round(max(0, value), 2)


def period_date_range(period: str, year: Optional[int] = None) -> Tuple[str, str, str]:
    from services.academic_calendar_service import period_range
    return period_range(period, year)


def _average(values: List[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def build_student_grade_rows(students: List[Dict[str, Any]], results: List[Dict[str, Any]], policy=None) -> List[Dict[str, Any]]:
    notes_by_student: Dict[int, List[Dict[str, Any]]] = {}
    for item in academic_notes(results):
        if item.get('activity_type') == 'juegos':
            continue
        student_id = int(item.get('student_id') or 0)
        notes_by_student.setdefault(student_id, []).append(item)

    rows = []
    for index, student in enumerate(students or [], start=1):
        student_id = int(student.get('id') or 0)
        notes = notes_by_student.get(student_id, [])
        activity_scores = [to_scale_20(item.get('score')) for item in notes if item.get('activity_type') == 'actividades']
        evaluation_scores = [to_scale_20(item.get('score')) for item in notes if item.get('activity_type') == 'evaluaciones']
        average = academic_average(notes, policy)
        level = achievement_level(average) if average is not None else {'code': '-', 'label': 'Pendiente'}
        first = student.get('first_name') or ''
        last = student.get('last_name') or ''
        rows.append({
            'n': index,
            'student_id': student_id,
            'code': student.get('student_code') or f'ALU-{student_id:04d}',
            'student_name': f'{first} {last}'.strip() or f'Estudiante {student_id}',
            'grade': int(student.get('grade') or 0),
            'section': (student.get('section') or '').upper(),
            'activities': _average(activity_scores),
            'evaluations': _average(evaluation_scores),
            'average': average,
            'components': component_summary(notes, policy)['scores'] if policy and policy.get('mode') == 'components' else {},
            'level': level['code'],
            'level_label': level['label'],
        })
    rows.sort(key=lambda row: (-(row['average'] if row['average'] is not None else -1), row['student_name']))
    for index, row in enumerate(rows, start=1):
        row['n'] = index
    return rows


def build_academic_report(
    students: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    grade: Optional[int] = None,
    section: Optional[str] = None,
    period: str = '1',
    policy=None,
) -> Dict[str, Any]:
    date_from, date_to, period_label = period_date_range(period)
    filtered_students = list(students or [])
    if grade:
        filtered_students = [student for student in filtered_students if int(student.get('grade') or 0) == int(grade)]
    if section and section.lower() != 'all':
        filtered_students = [
            student for student in filtered_students
            if str(student.get('section') or 'A').upper() == str(section).upper()
        ]

    student_ids = {int(student.get('id') or 0) for student in filtered_students}
    filtered_results = [
        item for item in (results or [])
        if int(item.get('student_id') or 0) in student_ids
        and ((int(item.get('academic_year') or 0) == int(date_from[:4]) and str(item.get('period')) == str(period))
             if item.get('grade_component') else date_from <= str(item.get('created_at') or '')[:10] <= date_to)
    ]
    rows = build_student_grade_rows(filtered_students, filtered_results, policy)

    counts = {'AD': 0, 'A': 0, 'B': 0, 'C': 0}
    for row in rows:
        counts[row['level']] = counts.get(row['level'], 0) + 1
    averages = [row['average'] for row in rows if row['average'] is not None]
    return {
        'grade': int(grade) if grade else None,
        'grade_label': GRADE_LABELS.get(int(grade), 'Todos los grados') if grade else 'Todos los grados',
        'section': (section or 'A').upper() if section and section.lower() != 'all' else 'Todas',
        'policy': policy,
        'average_status': 'weighted' if policy else 'provisional',
        'period': str(period),
        'period_label': period_label,
        'date_from': date_from,
        'date_to': date_to,
        'average': _average(averages) if averages or not policy or policy.get('mode') != 'components' else None,
        'students_count': len(rows),
        'counts': {
            'destacado': counts['AD'],
            'esperado': counts['A'],
            'proceso': counts['B'],
            'apoyo': counts['C'],
        },
        'chart': [
            {'label': 'Logro destacado (AD)', 'value': counts['AD'], 'color': '#16a34a'},
            {'label': 'Logro esperado (A)', 'value': counts['A'], 'color': '#2563eb'},
            {'label': 'En proceso (B)', 'value': counts['B'], 'color': '#f59e0b'},
            {'label': 'Necesita apoyo (C)', 'value': counts['C'], 'color': '#dc2626'},
        ],
        'rows': rows,
    }


def build_report_summary(students: List[Dict[str, Any]], topics: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_students = len(students or [])
    total_topics = len(topics or [])
    grade_report = {}
    for student in students or []:
        grade = str(student.get('grade', 0))
        grade_report.setdefault(grade, {'students': 0, 'avg_progress': 0})
        grade_report[grade]['students'] += 1
        grade_report[grade]['avg_progress'] += int(student.get('progress', 0) or 0)

    for grade, data in grade_report.items():
        data['avg_progress'] = round(data['avg_progress'] / max(1, data['students']))

    return {
        'total_students': total_students,
        'total_topics': total_topics,
        'report_by_grade': grade_report,
        'general_average': round(
            sum(int(student.get('progress', 0) or 0) for student in students or []) / max(1, total_students)
        ) if students else 0,
    }


def build_student_risk_analysis(student: Dict[str, Any]) -> Dict[str, Any]:
    from services.ml.prediction_service import get_risk_prediction_service
    prediction_service = get_risk_prediction_service()
    student_id = student.get('id') or student.get('student_id')

    if student_id and prediction_service.is_available():
        pred = prediction_service.predict_for_student(int(student_id))
        if pred.get('success') and pred.get('risk_probability') is not None:
            return {
                'student_name': f"{student.get('first_name', 'Estudiante')} {student.get('last_name', '')}".strip(),
                'risk_level': pred.get('risk_level', 'Bajo').lower(),
                'recommendation': 'Intervención recomendada por modelo de Machine Learning supervisado.' if pred.get('risk_level') == 'Alto' else 'Seguimiento pedagógico regular.',
                'progress': int(student.get('progress', 0) or 0),
                'method': 'supervised_ml',
                'model_version': pred.get('model_version'),
            }

    unavailable = pred if student_id and prediction_service.is_available() else {}
    return {
        'student_name': f"{student.get('first_name', 'Estudiante')} {student.get('last_name', '')}".strip(),
        'risk_level': 'no disponible', 'risk_probability': None,
        'recommendation': unavailable.get('message') or 'Se necesita un alumno con historial y un modelo disponible para estimar riesgo.',
        'progress': int(student.get('progress', 0) or 0), 'method': 'unavailable',
        'ml_status': unavailable.get('code', 'MODEL_NOT_AVAILABLE' if student_id else 'STUDENT_REQUIRED'),
        'notice': 'No se ha calculado una clasificación de riesgo.',
    }
