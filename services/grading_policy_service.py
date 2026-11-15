from math import isfinite
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from config import Config

_policy = None
COMPONENTS = (
    ('homework', 'Revisión de tareas'),
    ('participation', 'Participación'),
    ('book', 'Revisión del libro'),
    ('practice_1', 'Práctica 1'),
    ('practice_2', 'Práctica 2'),
    ('exam', 'Examen bimestral'),
)
DEFAULT_COMPONENT_WEIGHTS = {key: (50 if key == 'exam' else 10) for key, _ in COMPONENTS}


def validate_component_weights(values):
    try:
        weights = {key: int(str(values[key])) for key, _ in COMPONENTS}
    except (KeyError, TypeError, ValueError):
        raise ValueError('Indica un porcentaje entero para cada componente.') from None
    if any(value < 0 or value > 100 for value in weights.values()) or sum(weights.values()) != 100:
        raise ValueError('Los seis porcentajes deben estar entre 0 y 100 y sumar 100.')
    if weights['exam'] <= max(value for key, value in weights.items() if key != 'exam'):
        raise ValueError('El examen debe pesar más que cada uno de los otros componentes.')
    return weights


def save_component_policy(values):
    global _policy
    weights = validate_component_weights(values)
    policy = {'mode': 'components', 'weights': weights}
    if Config.USE_MOCK_DATA:
        _policy = policy
    else:
        from services.db_service import get_connection
        with get_connection() as conn:
            conn.execute('INSERT INTO grading_component_policy '
                         '(id,homework,participation,book,practice_1,practice_2,exam) VALUES (1,%s,%s,%s,%s,%s,%s) '
                         'ON CONFLICT(id) DO UPDATE SET homework=EXCLUDED.homework,participation=EXCLUDED.participation,'
                         'book=EXCLUDED.book,practice_1=EXCLUDED.practice_1,practice_2=EXCLUDED.practice_2,exam=EXCLUDED.exam',
                         tuple(weights[key] for key, _ in COMPONENTS))
    return policy


def component_summary(results, policy):
    weights = validate_component_weights(policy['weights'])
    latest = {}
    for row in academic_notes(results):
        key = row.get('grade_component')
        if key in weights:
            stamp = (str(row.get('created_at') or ''), int(row.get('id') or 0))
            previous = latest.get(key)
            if previous is None or stamp >= previous[0]:
                latest[key] = (stamp, row.get('score'))
    scores = {}
    for key, _ in COMPONENTS:
        value = latest.get(key, (None, None))[1]
        try:
            score = Decimal(str(value)) if value is not None and not isinstance(value, bool) else None
        except InvalidOperation:
            score = None
        scores[key] = float(score) if score is not None and score.is_finite() and 0 <= score <= 20 else None
    missing = [key for key, weight in weights.items() if weight and scores[key] is None]
    average = None
    if not missing:
        total = sum(Decimal(str(scores[key])) * weight for key, weight in weights.items() if weight)
        average = float((total / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    return {'scores': scores, 'weights': weights, 'missing': missing, 'average': average}


def get_policy():
    if Config.USE_MOCK_DATA:
        return _policy
    from services.db_service import get_connection
    with get_connection() as conn:
        row = conn.execute('SELECT homework,participation,book,practice_1,practice_2,exam FROM grading_component_policy WHERE id=1').fetchone()
        if row:
            return {'mode': 'components', 'weights': dict(row)}
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
    if policy and policy.get('mode') == 'components':
        return component_summary(results, policy)['average']
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
