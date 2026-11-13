from datetime import datetime
import unicodedata
import os
import json
import re
import psycopg
from psycopg import Error
from psycopg.rows import dict_row

from config import Config


def _use_mock():
    return Config.USE_MOCK_DATA


_MOCK_MATERIAL_REVIEWS = {}
_MOCK_PRESENTATION_REVIEWS = {}


def get_connection():
    if _use_mock():
        raise Error('Modo mock activo â€” no hay conexiÃ³n PostgreSQL')

    if Config.DATABASE_URL:
        try:
            from services.connection_pool import borrow_connection
            return borrow_connection(Config.DATABASE_URL, dict_row)
        except ImportError:
            pass
        return psycopg.connect(Config.DATABASE_URL, row_factory=dict_row, connect_timeout=10)

    return psycopg.connect(
        host=os.getenv('POSTGRES_HOST', Config.POSTGRES_HOST),
        port=int(os.getenv('POSTGRES_PORT', Config.POSTGRES_PORT)),
        user=os.getenv('POSTGRES_USER', Config.POSTGRES_USER),
        password=os.getenv('POSTGRES_PASSWORD', Config.POSTGRES_PASSWORD),
        dbname=os.getenv('POSTGRES_DB', Config.POSTGRES_DB),
        row_factory=dict_row,
        connect_timeout=10,
    )


def ensure_schema(connection):
    """Compatibilidad de contrato: el esquema PostgreSQL se aplica con setup_db.py.

    La aplicaciÃ³n nunca crea ni altera tablas en tiempo de ejecuciÃ³n.
    """
    return True


def test_connection():
    if _use_mock():
        return True, 'Modo demostraciÃ³n (USE_MOCK_DATA=true)'
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True, f'Conectado a PostgreSQL Â· base: {Config.POSTGRES_DB}'
    except Error as e:
        return False, str(e)


def _query(sql, params=None, fetchone=False):
    conn = get_connection()
    try:
        cursor = conn.cursor(row_factory=dict_row)
        cursor.execute(sql, params or ())
        return cursor.fetchone() if fetchone else cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def _execute(sql, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor(row_factory=dict_row)
        statement = sql.strip()
        is_insert = statement.upper().startswith('INSERT INTO')
        if is_insert and ' RETURNING ' not in statement.upper():
            statement = f'{statement} RETURNING id'
        cursor.execute(statement, params or ())
        inserted = cursor.fetchone()['id'] if is_insert else cursor.rowcount
        conn.commit()
        return inserted
    finally:
        cursor.close()
        conn.close()


def _normalize_user_record(user):
    if not user or 'password_hash' in user:
        return user

    # Compatibilidad de lectura con la tabla users heredada de PostgreSQL.
    full_name = str(user.get('nombre_completo') or user.get('username') or '').strip()
    name_parts = full_name.split(maxsplit=1)
    grade_match = re.search(r'\d+', str(user.get('grado') or ''))
    grade = int(grade_match.group()) if grade_match else None
    legacy_role = str(user.get('rol') or '').strip().casefold()
    return {
        'id': user.get('id'),
        'username': user.get('username'),
        'password_hash': user.get('contrasena') or '',
        'role': 'teacher' if legacy_role in {'docente', 'profesor', 'teacher', 'admin'} else 'student',
        'first_name': name_parts[0] if name_parts else '',
        'last_name': name_parts[1] if len(name_parts) > 1 else '',
        'grade': grade,
        'section': user.get('section') or 'A',
    }


def fetch_user_by_username(username):
    if _use_mock():
        from services.mock_data import MOCK_USERS
        return MOCK_USERS.get(str(username or '').strip())
    username = str(username or '').strip()
    user = _query('SELECT * FROM users WHERE username = %s', (username,), fetchone=True)
    return _normalize_user_record(user)



def fetch_registered_students_for_messages():
    if _use_mock():
        from services.mock_data import MOCK_STUDENTS
        return [dict(s) for s in MOCK_STUDENTS]
    """Devuelve las cuentas de alumnos de users enlazadas con students para mensajes."""
    raw_users = _query('SELECT * FROM users ORDER BY id')
    student_rows = _query(
        "SELECT id, first_name, last_name, grade, COALESCE(section, 'A') AS section, "
        "COALESCE(student_code, CONCAT('ALU-', LPAD(id::text, 4, '0'))) AS student_code, "
        "progress, observations FROM students ORDER BY id"
    )

    def normalize_name(value):
        decomposed = unicodedata.normalize('NFKD', str(value or '').casefold())
        return ''.join(char for char in decomposed if char.isalnum())

    students_by_id = {int(row['id']): row for row in student_rows}
    students_by_name = {}
    for row in student_rows:
        key = (int(row['grade']), normalize_name(f"{row.get('first_name', '')} {row.get('last_name', '')}"))
        students_by_name.setdefault(key, row)

    registered_students = []
    for raw_user in raw_users:
        user = _normalize_user_record(raw_user)
        if not user or user.get('role') != 'student' or not user.get('grade'):
            continue

        grade = int(user['grade'])
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        student_row = students_by_id.get(int(user['student_id'])) if user.get('student_id') else None
        if not student_row:
            key = (grade, normalize_name(full_name))
            student_row = students_by_name.get(key)
        if not student_row:
            continue

        registered_students.append({
            **student_row,
            'id': int(student_row['id']),
            'first_name': user.get('first_name', ''),
            'last_name': user.get('last_name', ''),
            'grade': grade,
            'section': user.get('section') or student_row.get('section') or 'A',
        })

    return sorted(
        registered_students,
        key=lambda student: (student['grade'], student['last_name'].casefold(), student['first_name'].casefold()),
    )

def fetch_students():
    """Devuelve perfiles de estudiantes con cuenta registrada en PostgreSQL."""
    return fetch_registered_students_for_messages()


def ensure_student_records_for_registered_users():
    """Compatibilidad: no crear perfiles al cargar el panel docente."""
    return None


def fetch_topics_for_grade(grade, section=None):
    grade = int(grade) if grade else 5
    section = str(section or '').strip().upper() or None
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        topics = MOCK_TOPICS.get(grade, MOCK_TOPICS[5])
        return [
            topic for topic in topics
            if str(topic.get('status') or '').strip() == 'Publicado'
            and (
                not section
                or not topic.get('section')
                or str(topic.get('section')).strip().upper() == section
            )
        ]

    params = [grade, 'Publicado']
    section_clause = ''
    if section:
        section_clause = 'AND (section IS NULL OR UPPER(section) = %s) '
        params.append(section)
    return _query(
        'SELECT * FROM topics WHERE grade = %s AND status = %s '
        f'{section_clause}ORDER BY id',
        tuple(params),
    )


def fetch_all_topics():
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        topics = []
        for grade_topics in MOCK_TOPICS.values():
            topics.extend(grade_topics)
        return topics

    return _query('SELECT * FROM topics ORDER BY grade, id')


def fetch_student_progress(student_id):
    student_id = int(student_id) if student_id else 1
    if _use_mock():
        from services.mock_data import MOCK_PROGRESS
        return MOCK_PROGRESS.get(student_id, MOCK_PROGRESS[1])

    row = _query('SELECT * FROM student_progress WHERE student_id = %s', (student_id,), fetchone=True)
    if not row:
        return {'overall_progress': 0, 'completed_topics': 0, 'study_time': '0h', 'average_grade': 0}
    return row


def fetch_recommendations(student_id):
    if _use_mock():
        from services.mock_data import MOCK_RECOMMENDATIONS
        rows = MOCK_RECOMMENDATIONS
    else:
        rows = _query(
            'SELECT title, summary FROM ai_recommendations '
            'WHERE student_id = %s ORDER BY created_at DESC LIMIT 20',
            (student_id,),
        ) or []

    unique = []
    seen_types = set()
    for row in rows:
        title = str(row.get('title', ''))
        title_lower = title.lower()
        if 'actividades' in title_lower:
            recommendation_type = 'actividades'
        elif 'evaluaciones' in title_lower:
            recommendation_type = 'evaluaciones'
        elif 'juegos' in title_lower:
            recommendation_type = 'juegos'
        else:
            recommendation_type = title_lower
        if recommendation_type in seen_types:
            continue
        seen_types.add(recommendation_type)
        unique.append(row)
    return unique[:4]


def insert_recommendation(student_id, title, summary, topic_id=None):
    if _use_mock():
        return True
    return _execute(
        'INSERT INTO ai_recommendations (student_id, title, summary) VALUES (%s, %s, %s)',
        (student_id, title, summary),
    )


def insert_topic(title, description, grade, status='Pendiente', section=None, unit_number=None, session_number=None):
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        max_id = 0
        for grade_topics in MOCK_TOPICS.values():
            for topic in grade_topics:
                max_id = max(max_id, int(topic.get('id', 0)))
        new_topic = {
            'id': max_id + 1,
            'title': title,
            'description': description,
            'grade': int(grade),
            'status': status,
            'section': str(section).strip().upper() if section else None,
            'unit_number': int(unit_number) if unit_number else None,
            'session_number': int(session_number) if session_number else None,
        }
        MOCK_TOPICS.setdefault(int(grade), []).append(new_topic)
        return new_topic['id']
    return _execute(
        'INSERT INTO topics (title, description, grade, status, section, unit_number, session_number) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (title, description, int(grade), status, section, unit_number, session_number),
    )


def update_topic(topic_id, title=None, description=None, grade=None, status=None, section=None, unit_number=None, session_number=None):
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        for grade_topics in MOCK_TOPICS.values():
            for topic in grade_topics:
                if int(topic.get('id')) == int(topic_id):
                    if title is not None:
                        topic['title'] = title
                    if description is not None:
                        topic['description'] = description
                    if grade is not None:
                        topic['grade'] = int(grade)
                    if status is not None:
                        topic['status'] = status
                    if section is not None:
                        topic['section'] = str(section).strip().upper() or None
                    if unit_number is not None:
                        topic['unit_number'] = int(unit_number) if unit_number else None
                    if session_number is not None:
                        topic['session_number'] = int(session_number) if session_number else None
                    return topic
        return None

    updates = []
    params = []
    if title is not None:
        updates.append('title = %s')
        params.extend([title])
    if description is not None:
        updates.append('description = %s')
        params.extend([description])
    if grade is not None:
        updates.append('grade = %s')
        params.extend([int(grade)])
    if status is not None:
        updates.append('status = %s')
        params.extend([status])
    if section is not None:
        updates.append('section = %s')
        params.append(str(section).strip().upper() or None)
    if unit_number is not None:
        updates.append('unit_number = %s')
        params.append(int(unit_number) if unit_number else None)
    if session_number is not None:
        updates.append('session_number = %s')
        params.append(int(session_number) if session_number else None)
    if not updates:
        return None
    params.append(int(topic_id))
    _execute(f'UPDATE topics SET {", ".join(updates)} WHERE id = %s', tuple(params))
    return fetch_topic_by_id(topic_id)


def delete_topic(topic_id):
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        for grade in list(MOCK_TOPICS.keys()):
            MOCK_TOPICS[grade] = [topic for topic in MOCK_TOPICS[grade] if int(topic.get('id')) != int(topic_id)]
        return True
    _execute('DELETE FROM topics WHERE id = %s', (int(topic_id),))
    return True


def fetch_topic_by_id(topic_id):
    if _use_mock():
        from services.mock_data import MOCK_TOPICS
        for grade_topics in MOCK_TOPICS.values():
            for topic in grade_topics:
                if int(topic.get('id')) == int(topic_id):
                    return topic
        return None
    return _query('SELECT * FROM topics WHERE id = %s', (int(topic_id),), fetchone=True)


def insert_student(first_name, last_name, grade, section='A'):
    target_section = str(section or 'A').upper()
    student_id = _execute(
        'INSERT INTO students (first_name, last_name, grade, section, progress, observations) VALUES (%s, %s, %s, %s, 0, %s)',
        (first_name, last_name, int(grade), target_section, ''),
    )
    _execute(
        'INSERT INTO student_progress (student_id, overall_progress, completed_topics, study_time, average_grade) VALUES (%s, 0, 0, %s, 0)',
        (student_id, '0h'),
    )
    return fetch_student_by_id(student_id)


def fetch_student_by_id(student_id):
    if _use_mock():
        from services.mock_data import MOCK_STUDENTS
        return next((dict(s) for s in MOCK_STUDENTS if s['id'] == int(student_id)), None)
    return _query(
        "SELECT id, first_name, last_name, grade, COALESCE(section, 'A') AS section, "
        "COALESCE(student_code, CONCAT('ALU-', LPAD(id::text, 4, '0'))) AS student_code, "
        'progress, observations FROM students WHERE id = %s',
        (int(student_id),),
        fetchone=True,
    )


def ensure_student_record_for_user(user, section=None):
    """Devuelve un students.id vÃ¡lido para un usuario alumno."""
    target_section = str(section or user.get('section') or 'A').upper()
    candidate_id = user.get('student_id')
    if candidate_id:
        student = fetch_student_by_id(candidate_id)
        if student:
            if str(student.get('section') or 'A').upper() != target_section:
                _execute('UPDATE students SET section = %s WHERE id = %s', (target_section, int(student['id'])))
            return int(student['id'])

    first_name = (user.get('first_name') or user.get('username') or 'Estudiante').strip()
    last_name = (user.get('last_name') or '').strip()
    grade = int(user.get('grade') or 5)

    def normalized_name(value):
        decomposed = unicodedata.normalize('NFKD', str(value or '').casefold())
        return ''.join(char for char in decomposed if char.isalnum())

    target_name = normalized_name(f'{first_name} {last_name}')

    candidates = _query(
        'SELECT id, first_name, last_name, section FROM students WHERE grade = %s ORDER BY id',
        (grade,),
    )
    existing = next((item for item in candidates
                     if normalized_name(f"{item.get('first_name', '')} {item.get('last_name', '')}") == target_name), None)
    if existing:
        student_id = int(existing['id'])
        if str(existing.get('section') or 'A').upper() != target_section:
            _execute('UPDATE students SET section = %s WHERE id = %s', (target_section, student_id))
    else:
        student_id = _execute(
            'INSERT INTO students (first_name, last_name, grade, section, progress, observations) VALUES (%s, %s, %s, %s, 0, %s)',
            (first_name, last_name or 'Alumno', grade, target_section, ''),
        )
    if user.get('username') and 'student_id' in user:
        _execute('UPDATE users SET student_id = %s WHERE username = %s', (student_id, user['username']))
    return int(student_id)


def delete_student(student_id):
    _execute('DELETE FROM students WHERE id = %s', (int(student_id),))
    return True


def update_student_observations(student_id, observations):
    _execute('UPDATE students SET observations = %s WHERE id = %s', (observations, student_id))


def record_student_result(student_id, topic_id=None, activity_type='actividades', item_type='activity', score=None, correct_answers=0, wrong_answers=0, time_spent_seconds=0, percentage=None, created_at=None):
    # Games are training telemetry, never academic marks, including legacy callers.
    if activity_type == 'juegos':
        return False
    from services.grade_service import normalize_to_scale_20, score_20_to_percentage_100, percentage_100_to_score_20

    if score is not None:
        score_val = normalize_to_scale_20(score)
        if percentage is not None:
            try:
                pct_val = max(0.0, min(100.0, float(percentage)))
            except (TypeError, ValueError):
                pct_val = score_20_to_percentage_100(score_val)
        else:
            pct_val = score_20_to_percentage_100(score_val)
    else:
        pct_val = max(0.0, min(100.0, float(percentage or 0)))
        score_val = percentage_100_to_score_20(pct_val)

    if _use_mock():
        from services.mock_data import MOCK_STUDENT_NOTES
        record = {
            'student_id': int(student_id), 'topic_id': int(topic_id) if topic_id else None,
            'activity_type': activity_type, 'item_type': item_type,
            'score': score_val, 'percentage': pct_val,
            'correct_answers': correct_answers,
            'wrong_answers': wrong_answers, 'time_spent_seconds': time_spent_seconds,
        }
        if created_at is not None:
            record['created_at'] = str(created_at)
        MOCK_STUDENT_NOTES.append(record)
        return True

    if created_at is not None:
        return _execute(
            'INSERT INTO student_notes '
            '(student_id, topic_id, activity_type, item_type, score, percentage, correct_answers, wrong_answers, notes, time_spent_seconds, created_at) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (student_id, topic_id, activity_type, item_type, score_val, pct_val, correct_answers, wrong_answers, '', time_spent_seconds, created_at),
        )

    return _execute(
        'INSERT INTO student_notes '
        '(student_id, topic_id, activity_type, item_type, score, percentage, correct_answers, wrong_answers, notes, time_spent_seconds) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (student_id, topic_id, activity_type, item_type, score_val, pct_val, correct_answers, wrong_answers, '', time_spent_seconds),
    )


def fetch_or_create_student_by_code(student_code, grade=5, first_name=None, last_name=None):
    """Obtiene el ID del estudiante por su student_code institucional o crea el registro si no existe."""
    code = str(student_code).strip()
    if not code:
        raise ValueError("student_code no puede estar vacÃ­o")

    if _use_mock():
        from services.mock_data import MOCK_STUDENTS
        existing = next((s for s in MOCK_STUDENTS if s.get('student_code') == code), None)
        if existing:
            return existing['id']
        sid = max((s['id'] for s in MOCK_STUDENTS), default=0) + 1
        MOCK_STUDENTS.append({'id': sid, 'student_code': code, 'first_name': first_name or 'Estudiante',
                              'last_name': last_name or code, 'grade': int(grade), 'section': 'A'})
        return sid

    row = _query('SELECT id FROM students WHERE student_code = %s LIMIT 1', (code,), fetchone=True)
    if row:
        return int(row['id'])

    fn = first_name or 'Estudiante'
    ln = last_name or code
    student_id = _execute(
        'INSERT INTO students (student_code, first_name, last_name, grade, progress, observations) VALUES (%s, %s, %s, %s, 0, %s)',
        (code, fn, ln, int(grade), 'Importado de registro histÃ³rico'),
    )
    _execute(
        'INSERT INTO student_progress (student_id, overall_progress, completed_topics, study_time, average_grade) VALUES (%s, 0, 0, %s, 0)',
        (student_id, '0h'),
    )
    return int(student_id)


def insert_academic_outcome(student_id, academic_period=None, period_type='bimester', final_score=0.0,
                            final_percentage=None, failed_courses_count=0, attendance_percentage=None,
                            is_at_risk=0, risk_level='Bajo', risk_reasons=None,
                            academic_year=None, period=None, subject='ComputaciÃ³n', final_grade=None, final_status=None):
    """Inserta o actualiza el resultado acadÃ©mico real de un estudiante en un perÃ­odo."""
    from services.grade_service import normalize_to_scale_20, score_20_to_percentage_100

    if academic_year is None and academic_period and '-' in str(academic_period):
        parts = str(academic_period).split('-', 1)
        try:
            academic_year = int(parts[0])
            if period is None:
                period = parts[1]
        except ValueError:
            pass

    if academic_year is None:
        academic_year = 2024
    if period is None:
        period = "B1"
    if academic_period is None:
        academic_period = f"{academic_year}-{period}"

    if final_grade is not None and (final_score == 0.0 or final_score is None):
        final_score = final_grade

    status_str = str(final_status or '').strip().lower()
    if is_at_risk is not None:
        at_risk = 1 if is_at_risk else 0
        risk_level = 'Alto' if at_risk == 1 else 'Bajo'
    elif status_str in {'desaprobado', 'en_riesgo', 'reprobado', 'requiere_recuperacion', 'c'} or (final_score is not None and float(final_score) < 11.0):
        at_risk = 1
        risk_level = 'Alto'
    else:
        at_risk = 0
        risk_level = 'Bajo'

    score_val = normalize_to_scale_20(final_score)
    pct_val = score_20_to_percentage_100(score_val) if final_percentage is None else float(final_percentage)
    status_final_str = final_status or ('desaprobado' if at_risk == 1 else 'aprobado')

    if _use_mock():
        from services.mock_data import MOCK_ACADEMIC_OUTCOMES
        record = {
            'student_id': int(student_id),
            'academic_period': academic_period,
            'academic_year': int(academic_year),
            'period': str(period),
            'subject': subject or 'ComputaciÃ³n',
            'period_type': period_type,
            'final_score': score_val,
            'final_grade': score_val,
            'final_percentage': pct_val,
            'final_status': status_final_str,
            'failed_courses_count': int(failed_courses_count or 0),
            'attendance_percentage': float(attendance_percentage) if attendance_percentage is not None else None,
            'is_at_risk': at_risk,
            'risk_level': risk_level,
            'risk_reasons': risk_reasons,
        }
        MOCK_ACADEMIC_OUTCOMES[:] = [
            o for o in MOCK_ACADEMIC_OUTCOMES
            if not (o.get('student_id') == int(student_id) and 
                    (o.get('academic_period') == academic_period or 
                     (o.get('academic_year') == int(academic_year) and o.get('period') == str(period))))
        ]
        MOCK_ACADEMIC_OUTCOMES.append(record)
        return True

    sql = (
        'INSERT INTO student_academic_outcomes '
        '(student_id, academic_year, period, academic_period, period_type, subject, final_score, final_grade, '
        'final_percentage, final_status, failed_courses_count, attendance_percentage, is_at_risk, risk_level, risk_reasons) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
        'ON CONFLICT (student_id, academic_period) DO UPDATE SET '
        'final_score = EXCLUDED.final_score, final_grade = EXCLUDED.final_grade, '
        'final_percentage = EXCLUDED.final_percentage, final_status = EXCLUDED.final_status, '
        'failed_courses_count = EXCLUDED.failed_courses_count, attendance_percentage = EXCLUDED.attendance_percentage, '
        'is_at_risk = EXCLUDED.is_at_risk, risk_level = EXCLUDED.risk_level, risk_reasons = EXCLUDED.risk_reasons, '
        'recorded_at = CURRENT_TIMESTAMP'
    )
    return _execute(
        sql,
        (student_id, academic_year, period, academic_period, period_type, subject or 'ComputaciÃ³n',
         score_val, score_val, pct_val, status_final_str, failed_courses_count,
         attendance_percentage, at_risk, risk_level, risk_reasons)
    )


def fetch_academic_outcomes(student_id=None, academic_period=None, academic_year=None, period=None):
    """Obtiene los resultados acadÃ©micos histÃ³ricos."""
    if academic_period is None and academic_year and period:
        academic_period = f"{academic_year}-{period}"
    elif academic_period is None and academic_year:
        academic_period_prefix = f"{academic_year}-"
    else:
        academic_period_prefix = None

    if _use_mock():
        from services.mock_data import MOCK_ACADEMIC_OUTCOMES
        res = list(MOCK_ACADEMIC_OUTCOMES)
        if student_id:
            res = [r for r in res if int(r.get('student_id')) == int(student_id)]
        if academic_year:
            res = [r for r in res if int(r.get('academic_year', 0) or 0) == int(academic_year) or str(r.get('academic_period', '')).startswith(f"{academic_year}-")]
        if period:
            res = [r for r in res if str(r.get('period', '')).lower() == str(period).lower() or str(r.get('academic_period', '')).lower().endswith(f"-{str(period).lower()}")]
        if academic_period:
            res = [r for r in res if str(r.get('academic_period')) == str(academic_period) or f"{r.get('academic_year')}-{r.get('period')}" == str(academic_period)]
        elif academic_period_prefix:
            res = [r for r in res if str(r.get('academic_period', '')).startswith(academic_period_prefix) or str(r.get('academic_year', '')).startswith(str(academic_year))]
        return res

    clauses = ['1=1']
    params = []
    if student_id:
        clauses.append('student_id = %s')
        params.append(int(student_id))
    if academic_year:
        clauses.append('academic_year = %s')
        params.append(int(academic_year))
    if period:
        clauses.append('period = %s')
        params.append(str(period))
    if academic_period:
        clauses.append('(academic_period = %s OR CONCAT(academic_year, "-", period) = %s)')
        params.extend([academic_period, academic_period])
    elif academic_period_prefix:
        clauses.append('(academic_period LIKE %s OR academic_year = %s)')
        params.extend([f"{academic_period_prefix}%", int(academic_year)])

    sql = f'SELECT * FROM student_academic_outcomes WHERE {" AND ".join(clauses)} ORDER BY recorded_at DESC'
    return _query(sql, tuple(params)) or []


def fetch_student_activity_summary(student_id):
    if _use_mock():
        from services.mock_data import MOCK_STUDENT_NOTES
        notes = [item for item in MOCK_STUDENT_NOTES if item['student_id'] == int(student_id) and item.get('activity_type') != 'juegos']
        return {
            'activities': sum(item['activity_type'] == 'actividades' for item in notes),
            'evaluations': sum(item['activity_type'] == 'evaluaciones' for item in notes),
            'games': sum(item['activity_type'] == 'juegos' for item in notes),
            'best_score': max((item['score'] for item in notes), default=0),
            'average_score': round(sum(item['score'] for item in notes) / len(notes)) if notes else 0,
        }
    row = _query(
        'SELECT '
        'COUNT(*) AS total, '
        "COUNT(*) FILTER (WHERE activity_type = 'actividades') AS activities, "
        "COUNT(*) FILTER (WHERE activity_type = 'evaluaciones') AS evaluations, "
        "COUNT(*) FILTER (WHERE activity_type = 'juegos') AS games, "
        "COALESCE(MAX(score) FILTER (WHERE activity_type <> 'juegos'), 0) AS best_score, "
        "COALESCE(AVG(score) FILTER (WHERE activity_type <> 'juegos'), 0) AS average_score "
        'FROM student_notes WHERE student_id = %s',
        (student_id,),
        fetchone=True,
    ) or {}
    return {key: round(float(row.get(key, 0) or 0)) for key in ('activities', 'evaluations', 'games', 'best_score', 'average_score')}


def fetch_student_results(student_id=None, activity_type=None, date_from=None, date_to=None):
    if _use_mock():
        from services.mock_data import MOCK_STUDENT_NOTES
        rows = [dict(item) for item in MOCK_STUDENT_NOTES]
        return [row for row in rows if (not student_id or int(row.get('student_id')) == int(student_id)) and (not activity_type or row.get('activity_type') == activity_type)]
    clauses = ['1=1']
    params = []
    if student_id:
        clauses.append('n.student_id = %s')
        params.append(int(student_id))
    if activity_type:
        clauses.append('n.activity_type = %s')
        params.append(activity_type)
    if date_from:
        clauses.append('DATE(n.created_at) >= %s')
        params.append(date_from)
    if date_to:
        clauses.append('DATE(n.created_at) <= %s')
        params.append(date_to)
    return _query(
        "SELECT n.id, n.student_id, CONCAT(s.first_name, ' ', s.last_name) AS student_name, "
        'n.topic_id, t.title AS topic, n.activity_type, n.item_type, n.score, n.percentage, n.correct_answers, '
        'n.wrong_answers, n.time_spent_seconds, n.created_at '
        'FROM student_notes n LEFT JOIN students s ON s.id = n.student_id '
        'LEFT JOIN topics t ON t.id = n.topic_id WHERE ' + ' AND '.join(clauses) + ' '
        'ORDER BY n.created_at DESC', tuple(params),
    ) or []


fetch_student_notes = fetch_student_results


def fetch_topic_progress(student_id):
    if _use_mock():
        from services.mock_data import MOCK_STUDENT_NOTES, MOCK_TOPICS
        notes = [item for item in MOCK_STUDENT_NOTES if item['student_id'] == int(student_id) and item.get('activity_type') != 'juegos']
        topics = [topic for grade_topics in MOCK_TOPICS.values() for topic in grade_topics]
        topic_progress = []
        required_activities = {'actividades', 'evaluaciones'}
        for topic in topics:
            topic_notes = [item for item in notes if item.get('topic_id') == topic.get('id')]
            completed_activities = {
                item.get('activity_type')
                for item in topic_notes
                if item.get('activity_type') in required_activities
            }
            completed_count = len(completed_activities)
            topic_progress.append({
                'id': topic.get('id'),
                'title': topic.get('title'),
                'score': round(completed_count * 20 / 2, 2),
                'completed_activities': completed_count,
                'completed': completed_count == 2,
            })
        return topic_progress
    rows = _query(
        'SELECT t.id, t.title, '
        'ROUND((COUNT(DISTINCT n.activity_type) FILTER (WHERE n.activity_type IN (\'actividades\', \'evaluaciones\')) * 20.0 / 2)::numeric, 2)::double precision AS score, '
        'COUNT(DISTINCT n.activity_type) FILTER (WHERE n.activity_type IN (\'actividades\', \'evaluaciones\')) AS completed_activities, '
        'COUNT(DISTINCT n.activity_type) FILTER (WHERE n.activity_type IN (\'actividades\', \'evaluaciones\')) = 2 AS completed '
        'FROM topics t LEFT JOIN student_notes n ON n.topic_id = t.id AND n.student_id = %s '
        'GROUP BY t.id, t.title ORDER BY t.id',
        (student_id,),
    )
    return rows or []


def fetch_learning_materials(topic_id, student_id):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS
        reviewed_set = _MOCK_MATERIAL_REVIEWS.get(int(student_id), set())
        reviewed_presentations = _MOCK_PRESENTATION_REVIEWS.get(int(student_id), set())
        materials = [
            dict(item, reviewed=(int(item['id']) in reviewed_set), source='material')
            for item in MOCK_MATERIALS
            if int(item['topic_id']) == int(topic_id)
            and str(item.get('status') or 'PUBLISHED').upper() == 'PUBLISHED'
        ]
        return materials + [
            dict(item, source='presentation', reviewed=(int(item['id']) in reviewed_presentations), material_type='presentacion', description=item.get('description') or 'Archivo del tema', content='')
            for item in get_presentations_for_topic(topic_id, published_only=True)
        ]
    materials = _query(
        'SELECT m.id, m.topic_id, m.title, m.material_type, m.description, m.content, m.resource_url, m.status, '
        'CASE WHEN r.id IS NULL THEN FALSE ELSE TRUE END AS reviewed '
        'FROM learning_materials m LEFT JOIN material_reviews r '
        'ON r.material_id = m.id AND r.student_id = %s '
        "WHERE m.topic_id = %s AND m.status = 'PUBLISHED' ORDER BY m.id",
        (student_id, topic_id),
    ) or []
    for material in materials:
        material['source'] = 'material'
    presentations = get_presentations_for_topic(topic_id, published_only=True)
    reviewed_presentations = {
        int(row['presentation_id'])
        for row in _query(
            'SELECT presentation_id FROM student_presentation_reviews '
            'WHERE student_id = %s AND presentation_id IN '
            '(SELECT id FROM topic_presentations WHERE topic_id = %s)',
            (student_id, topic_id),
        ) or []
    }
    for presentation in presentations:
        session_number = presentation.get('session_number') or 1
        title = str(presentation.get('title') or '').strip()
        file_name = str(presentation.get('file_name') or '').strip()
        title = title or file_name or f"Sesión {session_number}"
        description = str(presentation.get('description') or '').strip()
        description = description or f"Archivo de sesión {session_number}"
        for field_name, value in (('title', title), ('description', description)):
            if chr(195) in value or chr(194) in value:
                try:
                    repaired = value.encode('latin-1').decode('utf-8')
                    if repaired:
                        if field_name == 'title':
                            title = repaired
                        else:
                            description = repaired
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
        materials.append({
            'id': presentation['id'],
            'topic_id': topic_id,
            'title': title,
            'material_type': 'presentacion',
            'description': description,
            'content': '',
            'resource_url': f"/student/api/presentations/{presentation['id']}/file",
            'file_path': presentation.get('file_path'),
            'file_name': presentation.get('file_name'),
            'status': presentation.get('status', 'PUBLISHED'),
            'reviewed': int(presentation['id']) in reviewed_presentations,
            'source': 'presentation',
        })
    return materials


def mark_material_reviewed(material_id, student_id, source='material'):
    if _use_mock():
        student_key = int(student_id)
        review_sets = _MOCK_PRESENTATION_REVIEWS if source == 'presentation' else _MOCK_MATERIAL_REVIEWS
        reviewed = review_sets.setdefault(student_key, set())
        reviewed.add(int(material_id))
        return True
    if source == 'presentation':
        return _execute(
            'INSERT INTO student_presentation_reviews (presentation_id, student_id) VALUES (%s, %s) '
            'ON CONFLICT (presentation_id, student_id) DO UPDATE SET reviewed_at = CURRENT_TIMESTAMP',
            (material_id, student_id),
        )
    return _execute(
        'INSERT INTO material_reviews (material_id, student_id) VALUES (%s, %s) '
        'ON CONFLICT (material_id, student_id) DO UPDATE SET reviewed_at = CURRENT_TIMESTAMP',
        (material_id, student_id),
    )


def fetch_materials_for_teacher(topic_id):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS
        return [item for item in MOCK_MATERIALS if int(item['topic_id']) == int(topic_id)]
    return _query(
        'SELECT id, topic_id, title, material_type, description, content, resource_url, status '
        'FROM learning_materials WHERE topic_id = %s ORDER BY id',
        (topic_id,),
    ) or []


def create_learning_material(topic_id, title, material_type, description='', content='', resource_url='', status='DRAFT'):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS
        next_id = max((int(item['id']) for item in MOCK_MATERIALS), default=0) + 1
        MOCK_MATERIALS.append({
            'id': next_id, 'topic_id': int(topic_id), 'title': title,
            'material_type': material_type, 'description': description,
            'content': content, 'resource_url': resource_url, 'status': status,
        })
        return next_id
    return _execute(
        'INSERT INTO learning_materials (topic_id, title, material_type, description, content, resource_url, status) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (topic_id, title, material_type, description, content, resource_url, status),
    )


def update_learning_material_status(material_id, status):
    if status not in {'DRAFT', 'PUBLISHED'}:
        raise ValueError('Estado de material no vÃ¡lido')
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS
        for material in MOCK_MATERIALS:
            if int(material.get('id', 0)) == int(material_id):
                material['status'] = status
                return True
        return False
    _execute(
        'UPDATE learning_materials SET status = %s WHERE id = %s',
        (status, int(material_id)),
    )
    return True


def delete_learning_material(material_id):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS
        MOCK_MATERIALS[:] = [item for item in MOCK_MATERIALS if int(item['id']) != int(material_id)]
        return True
    _execute('DELETE FROM learning_materials WHERE id = %s', (material_id,))
    return True


def fetch_material_by_id(material_id):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS, MOCK_TOPICS
        all_topics = []
        for g_topics in MOCK_TOPICS.values():
            all_topics.extend(g_topics)
        mat = next((dict(item) for item in MOCK_MATERIALS if int(item['id']) == int(material_id)), None)
        if mat:
            topic = next((t for t in all_topics if int(t['id']) == int(mat['topic_id'])), {})
            mat['topic_title'] = topic.get('title', 'Tema')
            mat['grade'] = topic.get('grade')
            mat['source'] = 'material'
            return mat
        presentation = next((dict(p) for p in get_presentations_for_topic(4) if int(p['id']) == int(material_id)), None)
        if presentation:
            return {
                'id': presentation.get('id'),
                'topic_id': presentation.get('topic_id'),
                'title': presentation.get('title') or 'PresentaciÃ³n del docente',
                'material_type': 'presentacion',
                'description': presentation.get('description') or 'Archivo del docente',
                'content': '',
                'resource_url': f"/student/api/presentations/{presentation['id']}/file",
                'topic_title': 'Tema',
                'grade': None,
                'source': 'presentation',
            }
        return None
    row = _query(
        'SELECT m.id, m.topic_id, m.title, m.material_type, m.description, m.content, m.resource_url, m.status, '
        'm.created_at, t.title AS topic_title, t.grade, \n'
        "'material' AS source "
        'FROM learning_materials m LEFT JOIN topics t ON t.id = m.topic_id WHERE m.id = %s',
        (material_id,),
        fetchone=True,
    )
    if row:
        return row

    presentation = _query(
        'SELECT p.id, p.topic_id, p.title, p.description, p.status, p.file_path, p.file_name, '
        't.title AS topic_title, t.grade, \'presentation\' AS source '
        'FROM topic_presentations p INNER JOIN topics t ON t.id = p.topic_id WHERE p.id = %s',
        (material_id,),
        fetchone=True,
    )
    if presentation:
        presentation['material_type'] = 'presentacion'
        presentation['content'] = ''
        return presentation
    return None


def fetch_all_materials_for_student(student_id, grade=None, section=None):
    if _use_mock():
        from services.mock_data import MOCK_MATERIALS, MOCK_TOPICS
        reviewed_set = _MOCK_MATERIAL_REVIEWS.get(int(student_id), set())
        reviewed_presentations = _MOCK_PRESENTATION_REVIEWS.get(int(student_id), set())
        all_topics = {}
        for g_topics in MOCK_TOPICS.values():
            for t in g_topics:
                all_topics[int(t['id'])] = t
        result = []
        normalized_section = str(section or '').strip().upper() or None
        for item in MOCK_MATERIALS:
            topic = all_topics.get(int(item.get('topic_id', 0)), {})
            if str(topic.get('status') or '').strip() != 'Publicado':
                continue
            if str(item.get('status') or 'PUBLISHED').upper() != 'PUBLISHED':
                continue
            if grade is not None and topic.get('grade') is not None:
                if int(topic.get('grade', 0)) != int(grade):
                    continue
            if normalized_section and topic.get('section') and str(topic.get('section')).upper() != normalized_section:
                continue
            mat = dict(item)
            mat['topic_title'] = topic.get('title', 'Tema')
            mat['grade'] = topic.get('grade')
            mat['reviewed'] = int(item['id']) in reviewed_set
            mat['snippet'] = (mat.get('content') or mat.get('description') or '')[:140]
            result.append(mat)

        for topic_id, topic in all_topics.items():
            if str(topic.get('status') or '').strip() != 'Publicado':
                continue
            if normalized_section and topic.get('section') and str(topic.get('section')).upper() != normalized_section:
                continue
            if grade is not None and topic.get('grade') is not None and int(topic.get('grade', 0)) != int(grade):
                continue
            for presentation in get_presentations_for_topic(topic_id):
                if str(presentation.get('status') or 'PUBLISHED').upper() != 'PUBLISHED':
                    continue
                result.append({
                    'id': presentation.get('id'),
                    'topic_id': topic_id,
                    'title': presentation.get('title') or 'PresentaciÃ³n del docente',
                    'material_type': 'presentacion',
                    'description': presentation.get('description') or 'Archivo del docente',
                    'content': '',
                    'resource_url': f"/student/api/presentations/{presentation['id']}/file",
                    'file_path': presentation.get('file_path'),
                    'file_name': presentation.get('file_name'),
                    'status': presentation.get('status', 'PUBLISHED'),
                    'topic_title': topic.get('title', 'Tema'),
                    'grade': topic.get('grade'),
                    'reviewed': int(presentation.get('id', 0)) in reviewed_presentations,
                    'snippet': (presentation.get('description') or 'Archivo del docente')[:140],
                    'source': 'presentation',
                })
        return result

    result = []
    sql = (
        'SELECT m.id, m.topic_id, m.title, m.material_type, m.description, m.content, m.resource_url, m.status, '
        'm.created_at, t.title AS topic_title, t.grade, '
        'CASE WHEN r.id IS NULL THEN FALSE ELSE TRUE END AS reviewed '
        'FROM learning_materials m '
        'INNER JOIN topics t ON t.id = m.topic_id '
        'LEFT JOIN material_reviews r ON r.material_id = m.id AND r.student_id = %s '
        "WHERE t.status = %s AND m.status = 'PUBLISHED' "
    )
    params = [student_id, 'Publicado']
    if grade is not None:
        sql += 'AND t.grade = %s '
        params.append(grade)
    if section:
        sql += 'AND (t.section IS NULL OR UPPER(t.section) = %s) '
        params.append(str(section).strip().upper())
    sql += 'ORDER BY m.id DESC'
    rows = _query(sql, tuple(params)) or []
    for r in rows:
        r['snippet'] = (r.get('content') or r.get('description') or '')[:140]
        r['source'] = 'material'
        result.append(r)

    pres_sql = (
        'SELECT p.id, p.topic_id, p.title, p.description, p.status, p.file_path, p.file_path AS resource_url, p.file_name, '
        't.title AS topic_title, t.grade, CASE WHEN r.presentation_id IS NULL THEN FALSE ELSE TRUE END AS reviewed '
        'FROM topic_presentations p '
        'INNER JOIN topics t ON t.id = p.topic_id '
        'LEFT JOIN student_presentation_reviews r ON r.presentation_id = p.id AND r.student_id = %s '
        "WHERE t.status = %s AND p.status = 'PUBLISHED' "
    )
    pres_params = [student_id, 'Publicado']
    if grade is not None:
        pres_sql += 'AND t.grade = %s '
        pres_params.append(grade)
    if section:
        pres_sql += 'AND (t.section IS NULL OR UPPER(t.section) = %s) '
        pres_params.append(str(section).strip().upper())
    pres_sql += 'ORDER BY p.id DESC'
    for presentation in _query(pres_sql, tuple(pres_params)) or []:
        presentation['material_type'] = 'presentacion'
        presentation['content'] = ''
        presentation['resource_url'] = f"/student/api/presentations/{presentation['id']}/file"
        presentation['snippet'] = (presentation.get('description') or 'Archivo del docente')[:140]
        presentation['source'] = 'presentation'
        result.append(presentation)
    return result



def fetch_topic_learning_items(topic_id):
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        items = MOCK_TOPIC_ITEMS.get(int(topic_id), {})
        return items
    activities = _query('SELECT id, title, activity_type, question, options, correct_answer, score FROM topic_activities WHERE topic_id = %s ORDER BY id', (topic_id,)) or []
    for activity in activities:
        if isinstance(activity.get('options'), (str, bytes)):
            try:
                activity['options'] = json.loads(activity['options'])
            except (TypeError, ValueError):
                activity['options'] = []
    games = _query('SELECT id, name, description, rules, is_active FROM topic_games WHERE topic_id = %s ORDER BY id', (topic_id,)) or []
    evaluations = _query('SELECT id, difficulty, questions FROM topic_evaluations WHERE topic_id = %s ORDER BY id DESC', (topic_id,)) or []
    from services.ai_service import coerce_questions
    for evaluation in evaluations:
        evaluation['questions'] = coerce_questions(evaluation.get('questions'))
    return {'activities': activities, 'games': games, 'evaluations': evaluations}


def create_topic_activity(topic_id, title, activity_type, question, options, correct_answer, score=5):
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        item = {'id': len(MOCK_TOPIC_ITEMS.setdefault(int(topic_id), {}).setdefault('activities', [])) + 1, 'title': title, 'activity_type': activity_type, 'question': question, 'options': options or [], 'correct_answer': correct_answer, 'score': score}
        MOCK_TOPIC_ITEMS[int(topic_id)]['activities'].append(item)
        return item['id']
    import json
    return _execute('INSERT INTO topic_activities (topic_id, title, activity_type, question, options, correct_answer, score) VALUES (%s, %s, %s, %s, %s, %s, %s)', (topic_id, title, activity_type, question, json.dumps(options or []), correct_answer, score))


def fetch_game_by_id(game_id):
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        for items in MOCK_TOPIC_ITEMS.values():
            for game in items.get('games', []):
                if int(game.get('id')) == int(game_id):
                    return _normalize_game_payload(game)
        return None

    row = _query(
        'SELECT id, topic_id, name, description, rules FROM topic_games WHERE id = %s',
        (int(game_id),),
        fetchone=True,
    )
    return _normalize_game_payload(row) if row else None


def fetch_all_games_with_topics():
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS, MOCK_TOPICS
        games = []
        topic_lookup = {}
        for grade_topics in MOCK_TOPICS.values():
            for topic in grade_topics:
                topic_lookup[int(topic['id'])] = topic
        for topic_id, items in MOCK_TOPIC_ITEMS.items():
            topic = topic_lookup.get(int(topic_id), {})
            if str(topic.get('status') or '').strip() != 'Publicado':
                continue
            for game in items.get('games', []):
                games.append({
                    'id': game['id'],
                    'topic_id': int(topic_id),
                    'name': game.get('name', 'Juego'),
                    'description': game.get('description', ''),
                    'topic_title': topic.get('title', 'Tema'),
                    'grade': topic.get('grade', 5),
                    'section': topic.get('section'),
                    'source': 'ollama',
                })
        return games

    try:
        rows = _query(
            'SELECT g.id, g.topic_id, g.name, g.description, t.title AS topic_title, t.grade, t.section '
            'FROM topic_games g JOIN topics t ON t.id = g.topic_id '
            'WHERE COALESCE(g.is_active, TRUE) = TRUE AND t.status = %s ORDER BY g.id DESC',
            ('Publicado',),
        ) or []
    except Exception:
        rows = _query(
            'SELECT g.id, g.topic_id, g.name, g.description, t.title AS topic_title, t.grade, t.section '
            'FROM topic_games g JOIN topics t ON t.id = g.topic_id '
            'WHERE t.status = %s ORDER BY g.id DESC',
            ('Publicado',),
        ) or []
    for row in rows:
        row['source'] = 'ollama'
    return rows


def _normalize_game_payload(game):
    if not game:
        return None
    pares = []
    levels = []
    rules = game.get('rules')
    if isinstance(rules, (str, bytes)) and rules.strip():
        try:
            parsed = json.loads(rules)
            if isinstance(parsed, list):
                pares = parsed
            elif isinstance(parsed, dict):
                pares = parsed.get('pares') or []
                levels = parsed.get('niveles') or parsed.get('levels') or []
            else:
                levels = []
        except (TypeError, ValueError):
            pares = []
            levels = []
    else:
        levels = []
    if not levels and pares:
        levels = [{'nivel': 1, 'tipo': 'relacionar', 'titulo': 'Une las parejas', 'pares': pares}]
    return {
        'id': game.get('id'),
        'topic_id': game.get('topic_id'),
        'titulo': game.get('name') or game.get('titulo') or 'Juego educativo',
        'instrucciones': game.get('description') or game.get('instrucciones') or 'Arrastra cada tÃ©rmino a su definiciÃ³n.',
        'pares': pares,
        'niveles': levels,
    }


def create_topic_game(topic_id, name, description, rules):
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        item = {'id': len(MOCK_TOPIC_ITEMS.setdefault(int(topic_id), {}).setdefault('games', [])) + 1, 'name': name, 'description': description, 'rules': rules, 'is_active': True}
        MOCK_TOPIC_ITEMS[int(topic_id)]['games'].append(item)
        return item['id']
    return _execute('INSERT INTO topic_games (topic_id, name, description, rules, is_active) VALUES (%s, %s, %s, %s, TRUE)', (topic_id, name, description, rules))


def replace_topic_games(topic_id):
    """Evita acumular copias del juego al regenerar un tema."""
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        MOCK_TOPIC_ITEMS.setdefault(int(topic_id), {})['games'] = []
        return True
    _execute('DELETE FROM topic_games WHERE topic_id = %s', (topic_id,))
    return True


def create_topic_evaluation(topic_id, difficulty, questions):
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        item = {'id': len(MOCK_TOPIC_ITEMS.setdefault(int(topic_id), {}).setdefault('evaluations', [])) + 1, 'difficulty': difficulty, 'questions': questions}
        MOCK_TOPIC_ITEMS[int(topic_id)]['evaluations'].append(item)
        return item['id']
    import json
    return _execute('INSERT INTO topic_evaluations (topic_id, difficulty, questions) VALUES (%s, %s, %s)', (topic_id, difficulty, json.dumps(questions or [])))


def clear_topic_learning_items(topic_id):
    """Replaces generated content for a topic instead of accumulating duplicates."""
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        MOCK_TOPIC_ITEMS.pop(int(topic_id), None)
        return True
    for table in ('topic_activities', 'topic_games', 'topic_evaluations'):
        _execute(f'DELETE FROM {table} WHERE topic_id = %s', (topic_id,))
    return True


def delete_topic_learning_item(item_type, item_id):
    table_by_type = {'activity': 'topic_activities', 'game': 'topic_games', 'evaluation': 'topic_evaluations'}
    if item_type not in table_by_type:
        return False
    if _use_mock():
        from services.mock_data import MOCK_TOPIC_ITEMS
        for items in MOCK_TOPIC_ITEMS.values():
            key = {'activity': 'activities', 'game': 'games', 'evaluation': 'evaluations'}[item_type]
            items[key] = [item for item in items if int(item.get('id')) != int(item_id)]
        return True
    _execute(f'DELETE FROM {table_by_type[item_type]} WHERE id = %s', (item_id,))
    return True


def get_presentations_for_topic(topic_id, published_only=False):
    """Obtiene las presentaciones asociadas a un tema."""
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        presentations = [
            dict(item) for item in MOCK_PRESENTATIONS
            if int(item.get('topic_id', 0)) == int(topic_id)
        ]
        for presentation in presentations:
            presentation.setdefault('status', 'PUBLISHED')
        return [
            presentation for presentation in presentations
            if not published_only or presentation.get('status') == 'PUBLISHED'
        ]

    try:
        status_clause = "AND status = 'PUBLISHED' " if published_only else ''
        rows = _query(
            'SELECT id, topic_id, title, description, session_number, status, file_name, file_path, uploaded_at '
            f'FROM topic_presentations WHERE topic_id = %s {status_clause}ORDER BY session_number ASC',
            (topic_id,),
        )
        return rows or []
    except Exception:
        return []


def fetch_all_presentations():
    """Obtiene todas las presentaciones subidas por el profesor."""
    if _use_mock():
        return [
            {
                'id': 1,
                'topic_id': 1,
                'title': 'IntroducciÃ³n a ComputaciÃ³n - SesiÃ³n 1',
                'session_number': 1,
                'file_name': 'sesion1_computacion.pptx',
                'file_path': '/static/uploads/presentations/sesion1.pptx',
                'uploaded_at': '2026-09-06',
            }
        ]
    try:
        rows = _query(
            'SELECT id, topic_id, title, description, session_number, status, file_name, file_path, uploaded_at '
            'FROM topic_presentations ORDER BY session_number ASC, id DESC'
        )
        return rows or []
    except Exception:
        return []


def insert_presentation(topic_id, title, session_number, description, file_path, file_name, file_size, uploaded_by, status='DRAFT'):
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        next_id = max((int(item.get('id', 0)) for item in MOCK_PRESENTATIONS), default=0) + 1
        MOCK_PRESENTATIONS.append({
            'id': next_id,
            'topic_id': int(topic_id),
            'title': title,
            'description': description,
            'session_number': int(session_number),
            'file_path': file_path,
            'file_name': file_name,
            'file_size': int(file_size),
            'uploaded_by': uploaded_by,
            'status': status,
        })
        return next_id
    return _execute(
        'INSERT INTO topic_presentations '
        '(topic_id, title, description, session_number, file_path, file_name, file_size, uploaded_by, status) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (topic_id, title, description, session_number, file_path, file_name, file_size, uploaded_by, status),
    )


def delete_presentation(presentation_id):
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        MOCK_PRESENTATIONS[:] = [
            item for item in MOCK_PRESENTATIONS
            if int(item.get('id', 0)) != int(presentation_id)
        ]
        return True
    _execute('DELETE FROM topic_presentations WHERE id = %s', (presentation_id,))
    return True


def fetch_presentation_by_topic_session(topic_id, session_number):
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        return next((
            dict(item) for item in MOCK_PRESENTATIONS
            if int(item.get('topic_id', 0)) == int(topic_id)
            and int(item.get('session_number', 0)) == int(session_number)
        ), None)
    return _query(
        'SELECT id, topic_id, title, description, session_number, status, file_name, file_path, file_size, uploaded_at FROM topic_presentations WHERE topic_id = %s AND session_number = %s ORDER BY id DESC LIMIT 1',
        (int(topic_id), int(session_number)),
        fetchone=True,
    )


def update_presentation(presentation_id, title, description, file_path, file_name, file_size, status='DRAFT'):
    if status not in {'DRAFT', 'PUBLISHED'}:
        raise ValueError('Estado de presentaciÃ³n no vÃ¡lido')
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        for item in MOCK_PRESENTATIONS:
            if int(item.get('id', 0)) == int(presentation_id):
                item.update({
                    'title': title,
                    'description': description,
                    'file_path': file_path,
                    'file_name': file_name,
                    'file_size': int(file_size),
                    'status': status,
                })
                return True
        return True
    _execute(
        'UPDATE topic_presentations SET title = %s, description = %s, file_path = %s, file_name = %s, file_size = %s, status = %s, uploaded_at = NOW() WHERE id = %s',
        (title, description, file_path, file_name, int(file_size), status, int(presentation_id)),
    )
    return True


def update_presentation_status(presentation_id, status):
    if status not in {'DRAFT', 'PUBLISHED'}:
        raise ValueError('Estado de presentaciÃ³n no vÃ¡lido')
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS
        for presentation in MOCK_PRESENTATIONS:
            if int(presentation.get('id', 0)) == int(presentation_id):
                presentation['status'] = status
                return True
        return False
    _execute(
        'UPDATE topic_presentations SET status = %s WHERE id = %s',
        (status, int(presentation_id)),
    )
    return True


def fetch_presentation_by_id(presentation_id):
    if _use_mock():
        from services.mock_data import MOCK_PRESENTATIONS, MOCK_TOPICS
        all_topics = [t for grade_topics in MOCK_TOPICS.values() for t in grade_topics]
        pres = next((dict(p) for p in MOCK_PRESENTATIONS if int(p['id']) == int(presentation_id)), None)
        if pres:
            topic = next((t for t in all_topics if int(t['id']) == int(pres.get('topic_id', 0))), {})
            pres['topic_title'] = topic.get('title', 'Tema')
            pres['grade'] = topic.get('grade')
        return pres

    return _query(
        'SELECT p.id, p.topic_id, p.title, p.description, p.session_number, p.status, p.file_path, p.file_name, '
        'p.file_size, p.uploaded_by, p.uploaded_at, t.title AS topic_title, t.grade '
        'FROM topic_presentations p LEFT JOIN topics t ON t.id = p.topic_id WHERE p.id = %s',
        (int(presentation_id),),
        fetchone=True,
    )


# ============================================================
# FUNCIONES PARA MENSAJES PROFESOR-ALUMNO
# ============================================================

def send_message_to_student(student_id, message):
    """EnvÃ­a un mensaje de profesor a un estudiante"""
    if _use_mock():
        from services.mock_data import MOCK_MESSAGES
        messages = MOCK_MESSAGES.setdefault(int(student_id), [])
        next_id = max((int(item.get('id', 0)) for items in MOCK_MESSAGES.values() for item in items), default=0) + 1
        messages.insert(0, {
            'id': next_id,
            'message': message,
            'is_read': False,
            'created_at': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
        })
        return next_id

    return _execute(
        'INSERT INTO teacher_messages (student_id, message, is_read) VALUES (%s, %s, FALSE)',
        (student_id, message),
    )


def fetch_messages_for_student(student_id):
    """Obtiene todos los mensajes para un estudiante"""
    try:
        rows = _query(
            'SELECT id, message, is_read, created_at FROM teacher_messages WHERE student_id = %s ORDER BY created_at DESC',
            (student_id,),
        )
        return rows or []
    except Exception:
        return []


def fetch_read_messages_for_teacher():
    """Obtiene los mensajes leÃ­dos desde PostgreSQL."""
    try:
        return _query(
            "SELECT m.id, 'success' AS alert_type, 'message' AS source, "
            "CONCAT('Mensaje leÃ­do por ', s.first_name, ' ', s.last_name) AS title, "
            'm.message AS description, TRUE AS is_read, m.created_at '
            'FROM teacher_messages m JOIN students s ON s.id = m.student_id '
            'WHERE m.is_read = TRUE ORDER BY m.created_at DESC'
        ) or []
    except Exception:
        return []


def mark_message_as_read(message_id):
    """Marca un mensaje como leÃ­do"""
    return _execute(
        'UPDATE teacher_messages SET is_read = TRUE WHERE id = %s',
        (message_id,),
    )


def delete_teacher_message(message_id):
    """Elimina un mensaje del historial del profesor."""
    return _execute('DELETE FROM teacher_messages WHERE id = %s', (message_id,))


def create_student_submission(student_id, topic_id, title, file_path, file_name):
    if _use_mock():
        from services.mock_data import MOCK_SUBMISSIONS
        item = {
            'id': max((int(row.get('id', 0)) for row in MOCK_SUBMISSIONS), default=0) + 1,
            'student_id': int(student_id), 'topic_id': int(topic_id), 'title': title,
            'file_path': file_path, 'file_name': file_name, 'status': 'pendiente',
            'teacher_score': None, 'teacher_feedback': '', 'submitted_at': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
        }
        MOCK_SUBMISSIONS.insert(0, item)
        return item['id']
    return _execute(
        'INSERT INTO student_submissions (student_id, topic_id, title, file_path, file_name) VALUES (%s, %s, %s, %s, %s)',
        (student_id, topic_id, title, file_path, file_name),
    )


def fetch_submissions(student_id=None, topic_id=None):
    if _use_mock():
        from services.mock_data import MOCK_SUBMISSIONS
        rows = list(MOCK_SUBMISSIONS)
        if student_id is not None:
            rows = [row for row in rows if int(row['student_id']) == int(student_id)]
        if topic_id is not None:
            rows = [row for row in rows if int(row['topic_id']) == int(topic_id)]
        return rows
    where, params = [], []
    if student_id is not None:
        where.append('s.student_id = %s'); params.append(student_id)
    if topic_id is not None:
        where.append('s.topic_id = %s'); params.append(topic_id)
    clause = f"WHERE {' AND '.join(where)}" if where else ''
    return _query(
        'SELECT s.id, s.student_id, s.topic_id, s.title, s.file_path, s.file_name, s.status, '
        's.teacher_score, s.teacher_feedback, s.submitted_at, s.reviewed_at, '
        "CONCAT(st.first_name, ' ', st.last_name) AS student_name, st.grade AS student_grade, "
        't.title AS topic_title, t.grade AS topic_grade '
        'FROM student_submissions s JOIN students st ON st.id = s.student_id JOIN topics t ON t.id = s.topic_id '
        f'{clause} ORDER BY s.submitted_at DESC', params,
    ) or []


def review_student_submission(submission_id, score, feedback):
    if _use_mock():
        from services.mock_data import MOCK_SUBMISSIONS
        for row in MOCK_SUBMISSIONS:
            if int(row['id']) == int(submission_id):
                row.update({'status': 'revisado', 'teacher_score': float(score), 'teacher_feedback': feedback})
                return True
        return False
    return _execute(
        "UPDATE student_submissions SET status = 'revisado', teacher_score = %s, teacher_feedback = %s, reviewed_at = NOW() WHERE id = %s",
        (score, feedback, submission_id),
    )


def get_unread_messages_count(student_id):
    """Obtiene el nÃºmero de mensajes no leÃ­dos para un estudiante"""
    try:
        row = _query(
            'SELECT COUNT(*) as count FROM teacher_messages WHERE student_id = %s AND is_read = FALSE',
            (student_id,),
            fetchone=True,
        )
        return row['count'] if row else 0
    except Exception:
        return 0


# ============================================================
# FUNCIONES PARA ALERTAS
# ============================================================

def fetch_alerts_for_user(user_id=None, student_id=None, unread_only=False):
    """Obtiene alertas para un usuario o estudiante"""
    if _use_mock():
        from services.mock_data import MOCK_ALERTS
        return MOCK_ALERTS

    try:
        where_clauses = []
        params = []

        if user_id:
            where_clauses.append('target_user_id = %s')
            params.append(user_id)
        elif student_id:
            where_clauses.append('target_student_id = %s')
            params.append(student_id)

        if unread_only:
            where_clauses.append('is_read = FALSE')

        where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'
        sql = f'SELECT id, alert_type, title, description, is_read, created_at FROM alerts WHERE {where_clause} ORDER BY created_at DESC'

        rows = _query(sql, params)
        return rows or []
    except Exception:
        return []


def get_unread_alerts_count(user_id=None, student_id=None):
    """Obtiene el nÃºmero de alertas no leÃ­das"""
    if _use_mock():
        from services.mock_data import MOCK_ALERTS
        return len([a for a in MOCK_ALERTS if not a.get('is_read', False)])

    try:
        where_clauses = ['is_read = FALSE']
        params = []

        if user_id:
            where_clauses.append('target_user_id = %s')
            params.append(user_id)
        elif student_id:
            where_clauses.append('target_student_id = %s')
            params.append(student_id)

        where_clause = ' AND '.join(where_clauses)
        sql = f'SELECT COUNT(*) as count FROM alerts WHERE {where_clause}'

        row = _query(sql, params, fetchone=True)
        return row['count'] if row else 0
    except Exception:
        return 0


def mark_alert_as_read(alert_id):
    """Marca una alerta como leÃ­da"""
    if _use_mock():
        return True

    return _execute(
        'UPDATE alerts SET is_read = TRUE WHERE id = %s',
        (alert_id,),
    )


def create_alert(alert_type, title, description, target_user_id=None, target_student_id=None):
    """Crea una nueva alerta"""
    if _use_mock():
        return True

    return _execute(
        'INSERT INTO alerts (alert_type, title, description, target_user_id, target_student_id) VALUES (%s, %s, %s, %s, %s)',
        (alert_type, title, description, target_user_id, target_student_id),
    )


# ==========================================================
# GOAL 3 â€” Evaluaciones IA con Ciclo de AprobaciÃ³n Docente
# ==========================================================

VALID_ASSESSMENT_STATUSES = ('GENERATED', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED')


def create_assessment(topic_id, title, teacher_id=None, status='GENERATED'):
    status = status.upper() if status else 'GENERATED'
    if status not in VALID_ASSESSMENT_STATUSES:
        raise ValueError(f"Estado invÃ¡lido '{status}'. Permitidos: {VALID_ASSESSMENT_STATUSES}")

    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS
        next_id = max((int(item['id']) for item in MOCK_ASSESSMENTS), default=0) + 1
        record = {
            'id': next_id,
            'topic_id': int(topic_id),
            'teacher_id': int(teacher_id) if teacher_id is not None else None,
            'title': title,
            'status': status,
            'created_at': datetime.now().isoformat(),
        }
        MOCK_ASSESSMENTS.append(record)
        return next_id

    return _execute(
        'INSERT INTO assessment (topic_id, teacher_id, title, status) VALUES (%s, %s, %s, %s)',
        (int(topic_id), teacher_id, title, status),
    )


def update_assessment_status(assessment_id, status):
    status = status.upper() if status else 'PENDING_REVIEW'
    if status not in VALID_ASSESSMENT_STATUSES:
        raise ValueError(f"Estado invÃ¡lido '{status}'. Permitidos: {VALID_ASSESSMENT_STATUSES}")

    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS
        for a in MOCK_ASSESSMENTS:
            if int(a['id']) == int(assessment_id):
                a['status'] = status
                return True
        return False

    _execute('UPDATE assessment SET status = %s WHERE id = %s', (status, int(assessment_id)))
    return True


def fetch_assessment_by_id(assessment_id):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS, MOCK_ASSESSMENT_QUESTIONS, MOCK_TOPICS
        ass = next((dict(item) for item in MOCK_ASSESSMENTS if int(item['id']) == int(assessment_id)), None)
        if not ass:
            return None
        for grade_topics in MOCK_TOPICS.values():
            for t in grade_topics:
                if int(t['id']) == int(ass['topic_id']):
                    ass['topic_title'] = t['title']
                    ass['grade'] = t.get('grade')
                    break
        ass['questions'] = [dict(q) for q in MOCK_ASSESSMENT_QUESTIONS if int(q['assessment_id']) == int(assessment_id)]
        for q in ass['questions']:
            q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
        return ass

    ass = _query(
        'SELECT a.id, a.topic_id, a.teacher_id, a.title, a.status, a.created_at, t.title AS topic_title, t.grade '
        'FROM assessment a LEFT JOIN topics t ON t.id = a.topic_id WHERE a.id = %s',
        (int(assessment_id),),
        fetchone=True,
    )
    if not ass:
        return None
    questions = _query(
        'SELECT id, assessment_id, question, option_a, option_b, option_c, answer, approved, created_at '
        'FROM questions WHERE assessment_id = %s ORDER BY id',
        (int(assessment_id),),
    ) or []
    for q in questions:
        q['approved'] = bool(q.get('approved'))
        q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
    ass['questions'] = questions
    return ass


def fetch_assessments_for_topic(topic_id, status=None):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS, MOCK_ASSESSMENT_QUESTIONS
        result = []
        for item in MOCK_ASSESSMENTS:
            if int(item['topic_id']) == int(topic_id):
                if status and item.get('status') != status:
                    continue
                copy_item = dict(item)
                qs = [dict(q) for q in MOCK_ASSESSMENT_QUESTIONS if int(q['assessment_id']) == int(item['id'])]
                for q in qs:
                    q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
                copy_item['questions'] = qs
                copy_item['total_questions'] = len(qs)
                copy_item['approved_questions'] = sum(1 for q in qs if q.get('approved'))
                result.append(copy_item)
        return result

    sql = (
        'SELECT a.id, a.topic_id, a.teacher_id, a.title, a.status, a.created_at, t.title AS topic_title '
        'FROM assessment a LEFT JOIN topics t ON t.id = a.topic_id WHERE a.topic_id = %s '
    )
    params = [int(topic_id)]
    if status:
        sql += 'AND a.status = %s '
        params.append(status)
    sql += 'ORDER BY a.id DESC'
    rows = _query(sql, tuple(params)) or []
    for r in rows:
        qs = _query('SELECT id, approved FROM questions WHERE assessment_id = %s', (r['id'],)) or []
        r['total_questions'] = len(qs)
        r['approved_questions'] = sum(1 for q in qs if q.get('approved'))
    return rows


def fetch_all_assessments(status=None, grade=None, section=None, unit_number=None, session_number=None):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS, MOCK_ASSESSMENT_QUESTIONS, MOCK_TOPICS
        all_topics = {}
        for grade_topics in MOCK_TOPICS.values():
            for t in grade_topics:
                all_topics[int(t['id'])] = t
        result = []
        for item in MOCK_ASSESSMENTS:
            if status and item.get('status') != status:
                continue
            copy_item = dict(item)
            t = all_topics.get(int(item['topic_id']), {})
            if grade is not None and int(t.get('grade') or 0) != int(grade):
                continue
            if section and t.get('section') and str(t.get('section')).upper() != str(section).upper():
                continue
            if unit_number is not None and int(t.get('unit_number') or 0) != int(unit_number):
                continue
            if session_number is not None and int(t.get('session_number') or 0) != int(session_number):
                continue
            copy_item['topic_title'] = t.get('title', 'Tema')
            copy_item['grade'] = t.get('grade')
            copy_item['section'] = t.get('section')
            copy_item['unit_number'] = t.get('unit_number')
            copy_item['session_number'] = t.get('session_number')
            qs = [dict(q) for q in MOCK_ASSESSMENT_QUESTIONS if int(q['assessment_id']) == int(item['id'])]
            for q in qs:
                q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
            copy_item['questions'] = qs
            copy_item['total_questions'] = len(qs)
            copy_item['approved_questions'] = sum(1 for q in qs if q.get('approved'))
            result.append(copy_item)
        return result

    sql = (
        'SELECT a.id, a.topic_id, a.teacher_id, a.title, a.status, a.created_at, '
        't.title AS topic_title, t.grade, t.section, t.unit_number, t.session_number '
        'FROM assessment a LEFT JOIN topics t ON t.id = a.topic_id '
    )
    clauses = []
    params = []
    if status:
        clauses.append('a.status = %s')
        params.append(status)
    if grade is not None:
        clauses.append('t.grade = %s')
        params.append(int(grade))
    if section:
        clauses.append('(t.section IS NULL OR UPPER(t.section) = %s)')
        params.append(str(section).strip().upper())
    if unit_number is not None:
        clauses.append('t.unit_number = %s')
        params.append(int(unit_number))
    if session_number is not None:
        clauses.append('t.session_number = %s')
        params.append(int(session_number))
    if clauses:
        sql += 'WHERE ' + ' AND '.join(clauses) + ' '
    sql += 'ORDER BY a.id DESC'
    rows = _query(sql, tuple(params)) or []
    for r in rows:
        qs = _query('SELECT id, approved FROM questions WHERE assessment_id = %s', (r['id'],)) or []
        r['total_questions'] = len(qs)
        r['approved_questions'] = sum(1 for q in qs if q.get('approved'))
    return rows


def create_question(assessment_id, question, option_a, option_b, option_c, answer, approved=False):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_QUESTIONS
        next_id = max((int(item['id']) for item in MOCK_ASSESSMENT_QUESTIONS), default=0) + 1
        record = {
            'id': next_id,
            'assessment_id': int(assessment_id),
            'question': question,
            'option_a': option_a,
            'option_b': option_b,
            'option_c': option_c,
            'answer': answer,
            'approved': bool(approved),
            'created_at': datetime.now().isoformat(),
        }
        MOCK_ASSESSMENT_QUESTIONS.append(record)
        return next_id

    return _execute(
        'INSERT INTO questions (assessment_id, question, option_a, option_b, option_c, answer, approved) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (int(assessment_id), question, option_a, option_b, option_c, answer, bool(approved)),
    )


def update_question(question_id, question=None, option_a=None, option_b=None, option_c=None, answer=None, approved=None):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_QUESTIONS
        for q in MOCK_ASSESSMENT_QUESTIONS:
            if int(q['id']) == int(question_id):
                if question is not None:
                    q['question'] = question
                if option_a is not None:
                    q['option_a'] = option_a
                if option_b is not None:
                    q['option_b'] = option_b
                if option_c is not None:
                    q['option_c'] = option_c
                if answer is not None:
                    q['answer'] = answer
                if approved is not None:
                    q['approved'] = bool(approved)
                return True
        return False

    updates = []
    params = []
    if question is not None:
        updates.append('question = %s')
        params.append(question)
    if option_a is not None:
        updates.append('option_a = %s')
        params.append(option_a)
    if option_b is not None:
        updates.append('option_b = %s')
        params.append(option_b)
    if option_c is not None:
        updates.append('option_c = %s')
        params.append(option_c)
    if answer is not None:
        updates.append('answer = %s')
        params.append(answer)
    if approved is not None:
        updates.append('approved = %s')
        params.append(bool(approved))
    if not updates:
        return False
    params.append(int(question_id))
    _execute(f'UPDATE questions SET {", ".join(updates)} WHERE id = %s', tuple(params))
    return True


def delete_question(question_id):
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_QUESTIONS
        MOCK_ASSESSMENT_QUESTIONS[:] = [q for q in MOCK_ASSESSMENT_QUESTIONS if int(q['id']) != int(question_id)]
        return True
    _execute('DELETE FROM questions WHERE id = %s', (int(question_id),))
    return True


def approve_question(question_id, approved=True):
    return update_question(question_id, approved=approved)


def fetch_published_assessment_for_topic(topic_id):
    """
    Retorna la evaluaciÃ³n activa y PUBLICADA para un tema.
    FILTRO ESTRICTO: Ãšnicamente retorna preguntas con approved = TRUE.
    Si la evaluaciÃ³n estÃ¡ en GENERATED, PENDING_REVIEW o APPROVED (no publicada),
    retorna None (el alumno no puede verla).
    """
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENTS, MOCK_ASSESSMENT_QUESTIONS
        published = [
            item for item in MOCK_ASSESSMENTS
            if int(item['topic_id']) == int(topic_id) and item.get('status') == 'PUBLISHED'
        ]
        ass = dict(max(published, key=lambda item: int(item.get('id') or 0))) if published else None
        if not ass:
            return None
        approved_qs = []
        for q in MOCK_ASSESSMENT_QUESTIONS:
            if int(q['assessment_id']) == int(ass['id']) and q.get('approved'):
                copy_q = dict(q)
                copy_q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
                approved_qs.append(copy_q)
        ass['questions'] = approved_qs
        return ass

    ass = _query(
        'SELECT a.id, a.topic_id, a.teacher_id, a.title, a.status, a.created_at, t.title AS topic_title, t.grade '
        'FROM assessment a LEFT JOIN topics t ON t.id = a.topic_id '
        'WHERE a.topic_id = %s AND a.status = \'PUBLISHED\' ORDER BY a.id DESC',
        (int(topic_id),),
        fetchone=True,
    )
    if not ass:
        return None
    questions = _query(
        'SELECT id, assessment_id, question, option_a, option_b, option_c, answer, approved, created_at '
        'FROM questions WHERE assessment_id = %s AND approved = TRUE ORDER BY id',
        (ass['id'],),
    ) or []
    for q in questions:
        q['options'] = [q.get('option_a'), q.get('option_b'), q.get('option_c')]
    ass['questions'] = questions
    return ass


# ==========================================================
# GOAL 4 â€” Examen Ãšnico de 15 Preguntas e Intentos Formales
# ==========================================================

def record_student_assessment_attempt(
    student_id,
    assessment_id,
    score,
    time_spent,
    correct_answers=0,
    total_questions=15,
    percentage=0.0,
    reinforce_topics=None,
    answers=None,
):
    """
    Registra el intento formal de un alumno en la tabla student_assessment_attempts.
    Guarda: student_id, assessment_id, score, time_spent, date,
    asÃ­ como desglose de respuestas y temas a reforzar para retroalimentaciÃ³n formativa.
    """
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_ATTEMPTS
        next_id = max((int(item.get('id', 0)) for item in MOCK_ASSESSMENT_ATTEMPTS), default=0) + 1
        record = {
            'id': next_id,
            'student_id': int(student_id),
            'assessment_id': int(assessment_id),
            'score': float(score),
            'time_spent': int(time_spent),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'correct_answers': int(correct_answers),
            'total_questions': int(total_questions),
            'percentage': float(percentage),
            'reinforce_topics': list(reinforce_topics or []),
            'answers': dict(answers or {}),
        }
        MOCK_ASSESSMENT_ATTEMPTS.append(record)
        return next_id

    answers_payload = dict(answers or {})
    if reinforce_topics:
        answers_payload['reinforce_topics'] = list(reinforce_topics)
    answers_json = json.dumps(answers_payload, ensure_ascii=False)
    wrong_answers = max(0, int(total_questions) - int(correct_answers))
    return _execute(
        'INSERT INTO student_assessment_attempts '
        '(student_id, assessment_id, score, time_spent, correct_answers, total_questions, wrong_answers, answers) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (
            int(student_id),
            int(assessment_id),
            float(score),
            int(time_spent),
            int(correct_answers),
            int(total_questions),
            wrong_answers,
            answers_json,
        ),
    )


def fetch_student_assessment_attempts(student_id, assessment_id=None):
    """
    Recupera los intentos del estudiante ordenados cronolÃ³gicamente descendente.
    """
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_ATTEMPTS
        attempts = [
            dict(item) for item in MOCK_ASSESSMENT_ATTEMPTS
            if int(item.get('student_id', 0)) == int(student_id)
            and (assessment_id is None or int(item.get('assessment_id', 0)) == int(assessment_id))
        ]
        attempts.sort(key=lambda x: (x.get('date', ''), int(x.get('id', 0))), reverse=True)
        return attempts

    if assessment_id is not None:
        rows = _query(
            'SELECT id, student_id, assessment_id, score, time_spent, date, correct_answers, total_questions, wrong_answers, '
            'CASE WHEN total_questions > 0 THEN (correct_answers::numeric / total_questions) * 100 ELSE 0 END AS percentage, '
            'answers FROM student_assessment_attempts WHERE student_id = %s AND assessment_id = %s ORDER BY date DESC, id DESC',
            (int(student_id), int(assessment_id)),
        ) or []
    else:
        rows = _query(
            'SELECT id, student_id, assessment_id, score, time_spent, date, correct_answers, total_questions, wrong_answers, '
            'CASE WHEN total_questions > 0 THEN (correct_answers::numeric / total_questions) * 100 ELSE 0 END AS percentage, '
            'answers FROM student_assessment_attempts WHERE student_id = %s ORDER BY date DESC, id DESC',
            (int(student_id),),
        ) or []

    for r in rows:
        answers = r.get('answers')
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except Exception:
                answers = {}
        elif answers is None:
            answers = {}
        r['answers'] = answers
        reinforce_topics = r.get('reinforce_topics')
        if reinforce_topics is None:
            reinforce_topics = answers.get('reinforce_topics') if isinstance(answers, dict) else []
        if not isinstance(reinforce_topics, list):
            reinforce_topics = []
        r['reinforce_topics'] = reinforce_topics
    return rows


def fetch_assessment_attempt_by_id(attempt_id):
    """
    Obtiene un intento especÃ­fico por su ID.
    """
    if _use_mock():
        from services.mock_data import MOCK_ASSESSMENT_ATTEMPTS
        return next((dict(item) for item in MOCK_ASSESSMENT_ATTEMPTS if int(item.get('id', 0)) == int(attempt_id)), None)

    row = _query(
        'SELECT id, student_id, assessment_id, score, time_spent, date, correct_answers, total_questions, wrong_answers, '
        'CASE WHEN total_questions > 0 THEN (correct_answers::numeric / total_questions) * 100 ELSE 0 END AS percentage, '
        'answers FROM student_assessment_attempts WHERE id = %s',
        (int(attempt_id),),
        fetchone=True,
    )
    if row:
        answers = row.get('answers')
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except Exception:
                answers = {}
        elif answers is None:
            answers = {}
        row['answers'] = answers
        reinforce_topics = answers.get('reinforce_topics') if isinstance(answers, dict) else []
        row['reinforce_topics'] = reinforce_topics if isinstance(reinforce_topics, list) else []
    return row


def fetch_reinforcement_games_catalog():
    """
    Retorna los juegos interactivos de reforzamiento iniciales vinculados a temas curriculares.
    """
    from services.mock_data import MOCK_REINFORCEMENT_GAMES
    return [dict(g) for g in MOCK_REINFORCEMENT_GAMES]


def fetch_reinforcement_game_by_id(game_id):
    """
    Obtiene un juego de reforzamiento por su ID numÃ©rico.
    """
    games = fetch_reinforcement_games_catalog()
    return next((g for g in games if int(g.get('id', 0)) == int(game_id)), None)


def record_student_game_attempt(student_id, game_id, topic_id, game_type, score, is_correct, student_answer, time_spent=0, created_at=None):
    """
    Registra el intento y resultado del estudiante en la tabla student_game_attempts.
    """
    if created_at is None:
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if _use_mock():
        from services.mock_data import MOCK_GAME_ATTEMPTS
        attempt = {
            'id': len(MOCK_GAME_ATTEMPTS) + 1,
            'student_id': int(student_id),
            'game_id': int(game_id),
            'topic_id': int(topic_id),
            'game_type': str(game_type),
            'score': float(score),
            'is_correct': bool(is_correct),
            'student_answer': str(student_answer),
            'time_spent': int(time_spent),
            'created_at': str(created_at),
        }
        MOCK_GAME_ATTEMPTS.append(attempt)
        return attempt['id']

    return _execute(
        'INSERT INTO student_game_attempts (student_id, game_id, topic_id, game_type, score, is_correct, student_answer, time_spent, created_at) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (int(student_id), int(game_id), int(topic_id), str(game_type), float(score), bool(is_correct), str(student_answer), int(time_spent), str(created_at)),
    )


def fetch_student_game_attempts(student_id, game_id=None):
    """
    Retorna el historial de intentos de juegos de reforzamiento para un alumno.
    """
    if _use_mock():
        from services.mock_data import MOCK_GAME_ATTEMPTS
        attempts = [dict(a) for a in MOCK_GAME_ATTEMPTS if int(a.get('student_id', 0)) == int(student_id)]
        if game_id is not None:
            attempts = [a for a in attempts if int(a.get('game_id', 0)) == int(game_id)]
        attempts.sort(key=lambda a: a.get('id', 0), reverse=True)
        return attempts

    if game_id is not None:
        return _query(
            'SELECT id, student_id, game_id, topic_id, game_type, score, is_correct, student_answer, time_spent, created_at '
            'FROM student_game_attempts WHERE student_id = %s AND game_id = %s ORDER BY created_at DESC',
            (int(student_id), int(game_id)),
        ) or []

    return _query(
        'SELECT id, student_id, game_id, topic_id, game_type, score, is_correct, student_answer, time_spent, created_at '
        'FROM student_game_attempts WHERE student_id = %s ORDER BY created_at DESC',
        (int(student_id),),
    ) or []


def _normalize_ai_game_record(game):
    if not game:
        return None
    res = dict(game)
    content = res.get('content_json')
    if isinstance(content, str):
        try:
            res['content_json'] = json.loads(content)
        except Exception:
            pass
    return res


def create_ai_generated_game(topic_id, game_type, title, instruction, content_json, status='PENDING_REVIEW', material_id=None, presentation_id=None, created_by=None):
    """
    Guarda un nuevo juego educativo generado por IA con ciclo de aprobaciÃ³n docente.
    """
    if _use_mock():
        from services.mock_data import MOCK_AI_GENERATED_GAMES
        next_id = max((int(g.get('id', 0)) for g in MOCK_AI_GENERATED_GAMES), default=0) + 1
        record = {
            'id': next_id,
            'topic_id': int(topic_id),
            'material_id': int(material_id) if material_id else None,
            'presentation_id': int(presentation_id) if presentation_id else None,
            'game_type': str(game_type),
            'title': str(title),
            'instruction': str(instruction or ''),
            'content_json': content_json if isinstance(content_json, dict) else json.loads(content_json),
            'status': str(status or 'PENDING_REVIEW'),
            'created_by': int(created_by) if created_by else 1,
            'created_at': datetime.now().isoformat(),
        }
        MOCK_AI_GENERATED_GAMES.append(record)
        return next_id

    content_str = json.dumps(content_json, ensure_ascii=False) if isinstance(content_json, (dict, list)) else str(content_json)
    sql = (
        'INSERT INTO ai_generated_games (topic_id, material_id, presentation_id, game_type, title, instruction, content_json, status, created_by) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    return _execute(sql, (
        int(topic_id),
        int(material_id) if material_id else None,
        int(presentation_id) if presentation_id else None,
        game_type,
        title,
        instruction,
        content_str,
        status or 'PENDING_REVIEW',
        created_by,
    ))


def fetch_ai_generated_games(topic_id=None, status=None, presentation_id=None, material_id=None,
                             grade=None, section=None, unit_number=None, session_number=None):
    """
    Recupera juegos generados por IA filtrados opcionalmente por tema, estado, presentaciÃ³n o material.
    """
    if _use_mock():
        from services.mock_data import MOCK_AI_GENERATED_GAMES, MOCK_TOPICS
        all_topics = {}
        for grade_topics in MOCK_TOPICS.values():
            for t in grade_topics:
                all_topics[int(t['id'])] = t

        games = []
        for g in MOCK_AI_GENERATED_GAMES:
            if topic_id is not None and int(g.get('topic_id', 0)) != int(topic_id):
                continue
            if status is not None and g.get('status') != status:
                continue
            if presentation_id is not None and g.get('presentation_id') != int(presentation_id):
                continue
            if material_id is not None and g.get('material_id') != int(material_id):
                continue
            norm = _normalize_ai_game_record(g)
            t = all_topics.get(int(norm.get('topic_id', 0)), {})
            if grade is not None and int(t.get('grade') or 0) != int(grade):
                continue
            if section and t.get('section') and str(t.get('section')).upper() != str(section).upper():
                continue
            if unit_number is not None and int(t.get('unit_number') or 0) != int(unit_number):
                continue
            if session_number is not None and int(t.get('session_number') or 0) != int(session_number):
                continue
            norm['topic_title'] = t.get('title', 'Tema')
            norm['grade'] = t.get('grade')
            norm['section'] = t.get('section')
            norm['unit_number'] = t.get('unit_number')
            norm['session_number'] = t.get('session_number')
            games.append(norm)
        games.sort(key=lambda x: x.get('id', 0), reverse=True)
        return games

    clauses = ['1=1']
    params = []
    if topic_id is not None:
        clauses.append('g.topic_id = %s')
        params.append(int(topic_id))
    if status is not None:
        clauses.append('g.status = %s')
        params.append(str(status))
    if presentation_id is not None:
        clauses.append('g.presentation_id = %s')
        params.append(int(presentation_id))
    if material_id is not None:
        clauses.append('g.material_id = %s')
        params.append(int(material_id))
    if grade is not None:
        clauses.append('t.grade = %s')
        params.append(int(grade))
    if section:
        clauses.append('(t.section IS NULL OR UPPER(t.section) = %s)')
        params.append(str(section).strip().upper())
    if unit_number is not None:
        clauses.append('t.unit_number = %s')
        params.append(int(unit_number))
    if session_number is not None:
        clauses.append('t.session_number = %s')
        params.append(int(session_number))

    sql = (
        'SELECT g.*, t.title AS topic_title, t.grade, t.section, t.unit_number, t.session_number, '
        'p.file_name AS presentation_name, m.title AS material_title '
        'FROM ai_generated_games g '
        'LEFT JOIN topics t ON t.id = g.topic_id '
        'LEFT JOIN topic_presentations p ON p.id = g.presentation_id '
        'LEFT JOIN learning_materials m ON m.id = g.material_id '
        f'WHERE {" AND ".join(clauses)} ORDER BY g.id DESC'
    )
    rows = _query(sql, tuple(params)) or []
    return [_normalize_ai_game_record(r) for r in rows]


def fetch_ai_generated_game_by_id(game_id):
    """
    Obtiene un juego generado por IA segÃºn su identificador Ãºnico.
    """
    if _use_mock():
        from services.mock_data import MOCK_AI_GENERATED_GAMES, MOCK_TOPICS
        all_topics = {}
        for grade_topics in MOCK_TOPICS.values():
            for t in grade_topics:
                all_topics[int(t['id'])] = t
        for g in MOCK_AI_GENERATED_GAMES:
            if int(g.get('id', 0)) == int(game_id):
                norm = _normalize_ai_game_record(g)
                t = all_topics.get(int(norm.get('topic_id', 0)), {})
                norm['topic_title'] = t.get('title', 'Tema')
                return norm
        return None

    sql = (
        'SELECT g.*, t.title AS topic_title, p.file_name AS presentation_name, m.title AS material_title '
        'FROM ai_generated_games g '
        'LEFT JOIN topics t ON t.id = g.topic_id '
        'LEFT JOIN topic_presentations p ON p.id = g.presentation_id '
        'LEFT JOIN learning_materials m ON m.id = g.material_id '
        'WHERE g.id = %s'
    )
    row = _query(sql, (int(game_id),), fetchone=True)
    return _normalize_ai_game_record(row)


def update_ai_generated_game(game_id, title=None, instruction=None, content_json=None, status=None):
    """
    Actualiza datos o estado de un juego generado por IA.
    """
    if _use_mock():
        from services.mock_data import MOCK_AI_GENERATED_GAMES
        for g in MOCK_AI_GENERATED_GAMES:
            if int(g.get('id', 0)) == int(game_id):
                if title is not None:
                    g['title'] = str(title)
                if instruction is not None:
                    g['instruction'] = str(instruction)
                if content_json is not None:
                    g['content_json'] = content_json if isinstance(content_json, dict) else json.loads(content_json)
                if status is not None:
                    g['status'] = str(status)
                return True
        return False

    updates = []
    params = []
    if title is not None:
        updates.append('title = %s')
        params.append(str(title))
    if instruction is not None:
        updates.append('instruction = %s')
        params.append(str(instruction))
    if content_json is not None:
        updates.append('content_json = %s')
        params.append(json.dumps(content_json, ensure_ascii=False) if isinstance(content_json, (dict, list)) else str(content_json))
    if status is not None:
        updates.append('status = %s')
        params.append(str(status))

    if not updates:
        return True

    params.append(int(game_id))
    sql = f'UPDATE ai_generated_games SET {", ".join(updates)} WHERE id = %s'
    _execute(sql, tuple(params))
    return True


def update_ai_generated_game_status(game_id, status):
    """
    Modifica el estado del juego: GENERATED -> PENDING_REVIEW -> APPROVED -> PUBLISHED / REJECTED
    """
    return update_ai_generated_game(game_id, status=status)


def delete_ai_generated_game(game_id):
    """
    Elimina un juego generado por IA.
    """
    if _use_mock():
        from services.mock_data import MOCK_AI_GENERATED_GAMES
        initial_len = len(MOCK_AI_GENERATED_GAMES)
        MOCK_AI_GENERATED_GAMES[:] = [g for g in MOCK_AI_GENERATED_GAMES if int(g.get('id', 0)) != int(game_id)]
        return len(MOCK_AI_GENERATED_GAMES) < initial_len

    _execute('DELETE FROM ai_generated_games WHERE id = %s', (int(game_id),))
    return True


def fetch_published_ai_games_for_topic(topic_id=None):
    """
    Retorna ÃšNICAMENTE los juegos generados por IA que estÃ¡n en estado PUBLISHED para los alumnos.
    """
    filter_id = int(topic_id) if (topic_id and int(topic_id) != 0) else None
    return fetch_ai_generated_games(topic_id=filter_id, status='PUBLISHED')


def record_student_ai_game_attempt(student_id, game_id, topic_id, game_type, score, is_correct, student_answer, time_spent=10):
    """
    Registra el intento de un juego generado por IA en student_game_attempts y sincroniza student_notes.
    """
    return record_student_game_attempt(
        student_id=student_id,
        game_id=game_id,
        topic_id=topic_id,
        game_type=game_type,
        score=score,
        is_correct=is_correct,
        student_answer=student_answer,
        time_spent=time_spent
    )
