"""Auditable, reversible term closing with frozen scores and weights."""
from copy import deepcopy
from config import Config
from services import db_service
from services.grading_policy_service import COMPONENTS, get_policy, component_summary
from services.academic_calendar_service import get_calendar, period_range

_closures = {}
_events = []


def closed_periods(year, period, connection=None):
    if Config.USE_MOCK_DATA:
        return {key[0]: deepcopy(value) for key,value in _closures.items() if key[1:] == (year,period) and value['closed']}
    if connection is None:
        with db_service.get_connection() as conn:
            return closed_periods(year, period, conn)
    rows = connection.execute('SELECT * FROM bimester_closures WHERE academic_year=%s AND period=%s AND closed=TRUE', (year,period)).fetchall()
    return {int(row['grade']): dict(row) for row in rows}


def ensure_open(grade, year, period, connection=None):
    if connection is not None:
        connection.execute('SELECT pg_advisory_xact_lock(%s,%s)', (20261116, year*100+grade*10+period))
    if grade in closed_periods(year, period, connection):
        raise ValueError('El bimestre está cerrado. El docente debe reabrirlo antes de cambiar notas o vínculos.')


def change_closure(grade, year, period, action, reason, teacher_id):
    from services.bimester_grade_service import validate_term, component_results
    year, period, grade = validate_term(year, period, grade)
    reason = str(reason or '').strip()
    if action not in ('close','reopen') or not 5 <= len(reason) <= 500:
        raise ValueError('Indica el motivo del cierre o reapertura, entre 5 y 500 caracteres.')
    if action == 'close' and not get_calendar(year)['confirmed']:
        raise ValueError('Confirma primero el calendario real del colegio antes de cerrar el bimestre.')
    bounds = period_range(period, year)
    policy = get_policy()
    if not policy or policy.get('mode') != 'components':
        raise ValueError('Configura primero los seis porcentajes de calificación.')

    def execute(conn=None):
        if conn is not None:
            conn.execute('SELECT pg_advisory_xact_lock(%s,%s)', (20261116, year*100+grade*10+period))
        previous = closed_periods(year, period, conn).get(grade)
        if action == 'reopen':
            if not previous:
                raise ValueError('El bimestre no está cerrado.')
            snapshot = previous['snapshot']
        else:
            if previous:
                return previous
            if conn is None:
                students = [row for row in db_service.fetch_students() if int(row['grade']) == grade]
                results = db_service.fetch_student_results()
            else:
                students = conn.execute('SELECT DISTINCT s.* FROM students s JOIN users u ON u.student_id=s.id '
                                        "WHERE s.grade=%s AND u.role='student'", (grade,)).fetchall()
                results = conn.execute('SELECT n.* FROM student_notes n JOIN students s ON s.id=n.student_id WHERE s.grade=%s', (grade,)).fetchall()
            marks, _ = component_results(students, results, year, period, connection=conn, period_bounds=bounds)
            scores = {}
            for student in students:
                selected = [row for row in marks if int(row['student_id']) == int(student['id'])]
                scores[str(student['id'])] = component_summary(selected, policy)['scores']
            snapshot = {'policy': policy, 'scores': scores, 'date_from': bounds[0], 'date_to': bounds[1]}
        record = {'grade':grade,'academic_year':year,'period':period,'closed': action=='close', 'snapshot':snapshot}
        if conn is None:
            _closures[(grade,year,period)] = deepcopy(record)
            _events.append({'action':action,'reason':reason,'actor_id':teacher_id,**deepcopy(record)})
        else:
            from psycopg.types.json import Jsonb
            conn.execute('INSERT INTO bimester_closures(grade,academic_year,period,closed,snapshot,closed_by) '
                         'VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(grade,academic_year,period) DO UPDATE '
                         'SET closed=EXCLUDED.closed,snapshot=EXCLUDED.snapshot,closed_by=EXCLUDED.closed_by,closed_at=CURRENT_TIMESTAMP',
                         (grade,year,period,record['closed'],Jsonb(snapshot),teacher_id))
            conn.execute('INSERT INTO bimester_closure_events(grade,academic_year,period,action,reason,snapshot,actor_id) '
                         'VALUES(%s,%s,%s,%s,%s,%s,%s)', (grade,year,period,action,reason,Jsonb(snapshot),teacher_id))
        return record
    if Config.USE_MOCK_DATA:
        return execute()
    with db_service.get_connection() as connection:
        return execute(connection)
