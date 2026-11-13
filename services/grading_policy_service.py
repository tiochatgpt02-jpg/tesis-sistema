from math import isfinite
from config import Config

_policy = None


def get_policy():
    if Config.USE_MOCK_DATA:
        return _policy
    from services.db_service import get_connection
    with get_connection() as conn:
        return conn.execute('SELECT practice_weight,exam_weight FROM grading_policy WHERE id=1').fetchone()


def save_policy(practice, exam):
    global _policy
    practice, exam = int(practice), int(exam)
    if practice <= 0 or exam <= practice or practice + exam != 100:
        raise ValueError('Los pesos deben sumar 100; el examen debe pesar más que las prácticas y ambos deben ser positivos.')
    policy = {'practice_weight': practice, 'exam_weight': exam}
    if Config.USE_MOCK_DATA:
        _policy = policy
        return policy
    from services.db_service import get_connection
    with get_connection() as conn:
        conn.execute('INSERT INTO grading_policy (id,practice_weight,exam_weight) VALUES (1,%s,%s) '
                     'ON CONFLICT(id) DO UPDATE SET practice_weight=EXCLUDED.practice_weight,exam_weight=EXCLUDED.exam_weight',
                     (practice,exam))
    return policy


def academic_notes(results):
    """Most recent result per identified activity; game history never changes grades."""
    latest = {}
    legacy = []
    for row in results or []:
        if row.get('activity_type') == 'juegos':
            continue
        item = str(row.get('item_type') or '')
        if item.startswith(('practice:', 'exam:', 'submission:')):
            key = (row.get('student_id'), item)
            stamp = (str(row.get('created_at') or ''), int(row.get('id') or 0))
            previous = latest.get(key)
            if previous is None or stamp >= (str(previous.get('created_at') or ''), int(previous.get('id') or 0)):
                latest[key] = row
        else:
            legacy.append(row)
    return legacy + list(latest.values())


def academic_average(results, policy=None):
    notes = academic_notes(results)
    activities = [float(n.get('score') or 0) for n in notes if n.get('activity_type') == 'actividades']
    exams = [float(n.get('score') or 0) for n in notes if n.get('activity_type') == 'evaluaciones']
    values = activities + exams
    if not values:
        return None
    if not policy:
        return round(sum(values)/len(values),2)
    if not activities or not exams:
        return None
    value = (sum(activities)/len(activities)*policy['practice_weight'] + sum(exams)/len(exams)*policy['exam_weight'])/100
    return round(value,2) if isfinite(value) else None
