"""Six-component gradebook; manual marks and explicitly linked online assessments."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from config import Config
from services import db_service
from services.grading_policy_service import COMPONENTS, component_summary

_manual = {}
_sources = {}


def current_term():
    from services.academic_calendar_service import current_term as resolve_term
    return resolve_term()


def validate_term(year, period, grade=None):
    try:
        year, period = int(str(year)), int(str(period))
        grade = int(str(grade)) if grade is not None else None
    except (TypeError, ValueError):
        raise ValueError('Selecciona un año, bimestre y grado válidos.') from None
    if not 2000 <= year <= 2100 or period not in (1, 2, 3, 4) or grade not in (None, 4, 5, 6):
        raise ValueError('Selecciona un año, bimestre y grado válidos.')
    return year, period, grade


def source_options(grade):
    if Config.USE_MOCK_DATA:
        return []
    with db_service.get_connection() as conn:
        return conn.execute("SELECT 'practice:presentation:' || p.id AS value,'PPT: ' || p.title || ' - Sesión ' || p.session_number AS label,'practice' AS kind "
                            'FROM topic_presentations p JOIN topics t ON t.id=p.topic_id WHERE t.grade=%s '
                            "UNION ALL SELECT 'practice:material:' || m.id,'Material: ' || m.title,'practice' "
                            'FROM learning_materials m JOIN topics t ON t.id=m.topic_id WHERE t.grade=%s '
                            "UNION ALL SELECT (CASE WHEN a.kind='practice' THEN 'practice:' ELSE 'exam:' END) || a.id,"
                            "(CASE WHEN a.kind='practice' THEN 'Práctica: ' ELSE 'Examen: ' END) || a.title || ' (' || "
                            "(CASE WHEN a.status='PUBLISHED' THEN 'Publicado' WHEN a.status='APPROVED' THEN 'Por publicar' ELSE 'En revisión' END) || ')',a.kind "
                            'FROM assessment a JOIN topics t ON t.id=a.topic_id WHERE t.grade=%s ORDER BY label',
                            (grade, grade, grade)).fetchall()


def load_entries(year, period, connection=None):
    if Config.USE_MOCK_DATA:
        manual = [dict(value) for key, value in _manual.items() if key[1:3] == (year, period)]
        sources = [dict(value) for key, value in _sources.items() if key[1:3] == (year, period)]
        return manual, sources
    if connection is None:
        with db_service.get_connection() as conn:
            return load_entries(year, period, conn)
    manual = connection.execute('SELECT * FROM bimester_manual_grades WHERE academic_year=%s AND period=%s', (year, period)).fetchall()
    sources = connection.execute('SELECT * FROM bimester_component_sources WHERE academic_year=%s AND period=%s', (year, period)).fetchall()
    return manual, sources


def save_sources(grade, year, period, values, teacher_id):
    from services.academic_closure_service import ensure_open
    year, period, grade = validate_term(year, period, grade)
    options = {row['value']: row['kind'] for row in source_options(grade)}
    chosen = {key: str(values.get(key) or '').strip() for key in ('practice_1', 'practice_2', 'exam')}
    selected = [value for value in chosen.values() if value]
    if len(set(selected)) != len(selected):
        raise ValueError('Práctica 1 y práctica 2 deben corresponder a actividades diferentes.')
    for key, value in chosen.items():
        if value and options.get(value) != ('exam' if key == 'exam' else 'practice'):
            raise ValueError('La actividad seleccionada no corresponde al grado o componente.')
    if Config.USE_MOCK_DATA:
        ensure_open(grade, year, period)
        for key, value in chosen.items():
            identity = (grade, year, period, key)
            _sources.pop(identity, None)
            if value:
                _sources[identity] = dict(grade=grade, academic_year=year, period=period, component=key, source_item=value)
        return
    with db_service.get_connection() as conn:
        ensure_open(grade, year, period, conn)
        conn.execute('DELETE FROM bimester_component_sources WHERE grade=%s AND academic_year=%s AND period=%s', (grade, year, period))
        for key, value in chosen.items():
            if value:
                conn.execute('INSERT INTO bimester_component_sources (grade,academic_year,period,component,source_item,updated_by) '
                             'VALUES (%s,%s,%s,%s,%s,%s)', (grade, year, period, key, value, teacher_id))


def save_marks(student_id, year, period, values, teacher_id):
    from services.academic_closure_service import ensure_open
    year, period, _ = validate_term(year, period)
    student = db_service.fetch_student_by_id(student_id)
    if not student:
        raise ValueError('Alumno no encontrado.')
    validated = {}
    for key, _ in COMPONENTS:
        if key not in values:
            continue
        if key in ('practice_1', 'practice_2', 'exam'):
            raise ValueError('Las prácticas y el examen se califican automáticamente. Vincula la actividad correspondiente en la libreta.')
        raw = values[key]
        if raw is None or str(raw).strip() == '':
            validated[key] = None
            continue
        try:
            score = Decimal(str(raw)) if not isinstance(raw, bool) else Decimal('NaN')
        except InvalidOperation:
            raise ValueError('Las notas deben ser números entre 0 y 20.') from None
        if not score.is_finite() or not 0 <= score <= 20 or score.as_tuple().exponent < -2:
            raise ValueError('Las notas deben estar entre 0 y 20, con hasta dos decimales.')
        validated[key] = score
    if not validated:
        raise ValueError('No se recibieron notas para guardar.')
    if Config.USE_MOCK_DATA:
        ensure_open(int(student['grade']), year, period)
        for key, score in validated.items():
            identity = (int(student_id), year, period, key)
            _manual.pop(identity, None)
            if score is not None:
                _manual[identity] = dict(student_id=int(student_id), academic_year=year, period=period,
                                        component=key, score=score, updated_at=datetime.now(ZoneInfo('America/Lima')).isoformat())
        return
    with db_service.get_connection() as conn:
        ensure_open(int(student['grade']), year, period, conn)
        for key, score in validated.items():
            if score is None:
                conn.execute('DELETE FROM bimester_manual_grades WHERE student_id=%s AND academic_year=%s AND period=%s AND component=%s',
                             (student_id, year, period, key))
            else:
                conn.execute('INSERT INTO bimester_manual_grades (student_id,academic_year,period,component,score,updated_by) '
                             'VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(student_id,academic_year,period,component) '
                             'DO UPDATE SET score=EXCLUDED.score,updated_by=EXCLUDED.updated_by,updated_at=CURRENT_TIMESTAMP',
                             (student_id, year, period, key, score, teacher_id))


def component_results(students, results, year, period, connection=None, period_bounds=None):
    """Build explicit component marks; never guess a practice number from its position."""
    year, period, _ = validate_term(year, period)
    from services.teacher_reports_service import period_date_range
    date_from, date_to, _ = period_bounds or period_date_range(str(period), year)
    manual, sources = load_entries(year, period, connection)
    from services.academic_closure_service import closed_periods
    closed = closed_periods(year, period, connection)
    by_student = {int(student['id']): student for student in students}
    manual_map = {(int(row['student_id']), row['component']): row for row in manual}
    source_map = {(int(row['grade']), row['component']): row['source_item'] for row in sources}
    latest = {}
    for row in results:
        if row.get('activity_type') == 'juegos' or not date_from <= str(row.get('created_at') or '')[:10] <= date_to:
            continue
        key = (int(row.get('student_id') or 0), row.get('item_type'))
        previous = latest.get(key)
        if previous is None or (str(row.get('created_at') or ''), int(row.get('id') or 0)) > (str(previous.get('created_at') or ''), int(previous.get('id') or 0)):
            latest[key] = row
    output = []
    for student_id, student in by_student.items():
        closure = closed.get(int(student['grade']))
        if closure:
            scores = closure['snapshot']['scores'].get(str(student_id), {})
            for key, _ in COMPONENTS:
                if scores.get(key) is not None:
                    output.append({'id':0,'student_id':student_id,'score':scores[key],'grade_component':key,
                                   'item_type':f'component:{key}','activity_type':'component','academic_year':year,
                                   'period':period,'created_at':'','closed_policy':closure['snapshot']['policy']})
            continue
        for key, _ in COMPONENTS:
            source = source_map.get((int(student['grade']), key))
            automatic = key in ('practice_1', 'practice_2', 'exam')
            record = latest.get((student_id, source)) if automatic else manual_map.get((student_id, key))
            if record is None:
                continue
            output.append({
                'id': int(record.get('id') or 0), 'student_id': student_id,
                'student_name': f"{student.get('first_name') or ''} {student.get('last_name') or ''}".strip(),
                'score': float(record['score']), 'grade_component': key, 'item_type': f'component:{key}',
                'activity_type': 'component', 'academic_year': year, 'period': period,
                'created_at': str(record.get('updated_at') or record.get('created_at') or ''),
                'source_item': source,
            })
    return output, source_map


def grade_rows(students, results, year, period, policy):
    marks, sources = component_results(students, results, year, period)
    rows = []
    for student in students:
        student_id = int(student['id'])
        summary = component_summary([row for row in marks if row['student_id'] == student_id], policy)
        rows.append({'student': student, **summary,
                     'linked': {key: sources.get((int(student['grade']), key)) for key, _ in COMPONENTS},
                     'automatic': ('practice_1', 'practice_2', 'exam')})
    return rows


def with_component_results(students, results, policy, period, year=None):
    if not policy or policy.get('mode') != 'components':
        return results
    year = year or current_term()[0]
    marks, _ = component_results(students, results, year, period)
    return list(results) + marks
