"""Frozen questions and atomic academic submissions, independent of the LLM."""
import json
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from config import Config


class AttemptError(ValueError):
    pass


_attempts = {}
_permissions = {}
_lock = RLock()


@contextmanager
def _database():
    from services.db_service import get_connection
    with get_connection() as conn:
        yield conn


def _exam_lock(conn, student_id, assessment_id):
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                 (f'exam:{student_id}:{assessment_id}',))


def start_attempt(student_id, topic_id, kind, scope, questions, assessment_id=None):
    if not questions:
        raise AttemptError('No hay preguntas disponibles.')
    if kind not in {'practice', 'exam'}:
        raise AttemptError('Tipo de intento no válido.')
    # Freeze only the assessment contract. Database timestamps and other row
    # metadata do not belong to the JSON snapshot or the student's questions.
    fields = ('id', 'question', 'options', 'approved', 'subtopic', 'answer', 'correct_answer')
    questions = [{key: deepcopy(question[key]) for key in fields if key in question}
                 for question in questions]
    record = dict(id=str(uuid4()), student_id=int(student_id), topic_id=int(topic_id),
                  kind=kind, scope=str(scope), assessment_id=assessment_id,
                  questions=deepcopy(questions), started_at=datetime.now(timezone.utc), result=None)
    if Config.USE_MOCK_DATA:
        with _lock:
            if kind == 'exam':
                used = [a for a in _attempts.values() if a['student_id'] == int(student_id)
                        and a['assessment_id'] == assessment_id and a['kind'] == 'exam']
                pending = next((a for a in used if a['result'] is None), None)
                if pending:
                    return deepcopy(pending)
                if len(used) >= _permissions.get((int(student_id), assessment_id), 1):
                    raise AttemptError('Ya rendiste este examen. Solicita reapertura al profesor.')
            _attempts[record['id']] = deepcopy(record)
            return record
    with _database() as conn:
        if kind == 'exam':
            _exam_lock(conn, student_id, assessment_id)
            used = conn.execute(
                "SELECT * FROM learning_attempts WHERE student_id=%s AND kind='exam' AND assessment_id=%s ORDER BY started_at DESC",
                (student_id, assessment_id)).fetchall()
            pending = next((a for a in used if a['result'] is None), None)
            if pending:
                return {**pending, 'id': str(pending['id'])}
            permission = conn.execute('SELECT allowed_attempts FROM exam_permissions WHERE student_id=%s AND assessment_id=%s',
                                      (student_id, assessment_id)).fetchone()
            legacy = conn.execute('SELECT COUNT(*) AS n FROM student_assessment_attempts WHERE student_id=%s AND assessment_id=%s',
                                  (student_id, assessment_id)).fetchone()['n']
            if max(len(used), legacy) >= (permission['allowed_attempts'] if permission else 1):
                raise AttemptError('Ya rendiste este examen. Solicita reapertura al profesor.')
        conn.execute('INSERT INTO learning_attempts (id,student_id,topic_id,kind,scope,assessment_id,questions,started_at) '
                     'VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s)',
                     (record['id'], student_id, topic_id, kind, scope, assessment_id,
                      json.dumps(questions, ensure_ascii=False), record['started_at']))
    return record


def public_attempt(record):
    return {'attempt_id': str(record['id']), 'started_at': record['started_at'].isoformat(),
            'questions': [{k: q[k] for k in ('id', 'question', 'options', 'approved', 'subtopic') if k in q}
                          for q in record['questions']]}


def _grade(record, answers):
    if not isinstance(answers, dict):
        raise AttemptError('Las respuestas deben ser un objeto.')
    elapsed = max(1, int((datetime.now(timezone.utc) - record['started_at']).total_seconds()))
    if record['kind'] == 'exam' and elapsed > 30 * 60 + 30:
        raise AttemptError('El tiempo del examen terminó. Solicita reapertura al profesor.')
    graded = []
    for index, question in enumerate(record['questions']):
        received = str(answers.get(str(index), answers.get(str(question.get('id')), '')) or '').strip()
        expected = str(question.get('answer') or question.get('correct_answer') or '').strip()
        correct = bool(expected) and received.casefold() == expected.casefold()
        graded.append({'index': index, 'question': question.get('question'), 'expected': expected,
                       'received': received, 'correct': correct})
    count = sum(q['correct'] for q in graded)
    total = len(graded)
    weak_topics = list(dict.fromkeys(str(q.get('subtopic')) for q, g in zip(record['questions'], graded)
                                    if not g['correct'] and q.get('subtopic')))
    return {'correct_count': count, 'correct_answers': count, 'total': total, 'total_questions': total,
            'percentage': round(count / total * 100, 2), 'score': round(count / total * 20, 2),
            'score_20': round(count / total * 20, 2), 'time_spent': elapsed,
            'questions': graded, 'graded_questions': graded, 'reinforce_topics': weak_topics, 'recommended_games': []}


def submit_attempt(attempt_id, student_id, kind, scope, answers):
    if Config.USE_MOCK_DATA:
        with _lock:
            record = _attempts.get(str(attempt_id))
            _check(record, student_id, kind, scope)
            if record['result'] is not None:
                return deepcopy(record['result'])
            result = _grade(record, answers)
            from services.db_service import record_student_result, record_student_assessment_attempt
            record_student_result(student_id, record['topic_id'],
                                  'evaluaciones' if kind == 'exam' else 'actividades',
                                  f'{kind}:{scope}', result['score'], percentage=result['percentage'],
                                  correct_answers=result['correct_count'], wrong_answers=result['total']-result['correct_count'],
                                  time_spent_seconds=result['time_spent'])
            if kind == 'exam':
                result['assessment_attempt_id'] = record_student_assessment_attempt(
                    student_id, record['assessment_id'], result['score'], result['time_spent'],
                    result['correct_count'], result['total'], result['percentage'],
                    reinforce_topics=result['reinforce_topics'], answers=answers)
            record['result'] = deepcopy(result)
            return result
    with _database() as conn:
        if kind == 'exam':
            _exam_lock(conn, student_id, int(scope))
        record = conn.execute('SELECT * FROM learning_attempts WHERE id=%s FOR UPDATE', (attempt_id,)).fetchone()
        _check(record, student_id, kind, scope)
        if record['result'] is not None:
            return record['result']
        result = _grade(record, answers)
        if kind == 'exam':
            saved = conn.execute('INSERT INTO student_assessment_attempts '
                         '(student_id,assessment_id,score,time_spent,correct_answers,total_questions,wrong_answers,percentage,answers,reinforce_topics) '
                         'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb) RETURNING id',
                         (student_id,record['assessment_id'],result['score'],result['time_spent'],result['correct_count'],
                          result['total'],result['total']-result['correct_count'],result['percentage'],json.dumps(answers),
                          json.dumps(result['reinforce_topics']))).fetchone()
            result['assessment_attempt_id'] = saved['id']
        conn.execute('INSERT INTO student_notes (student_id,topic_id,activity_type,item_type,score,percentage,'
                     'correct_answers,wrong_answers,time_spent_seconds) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                     (student_id,record['topic_id'],'evaluaciones' if kind == 'exam' else 'actividades',
                      f'{kind}:{scope}',result['score'],result['percentage'],result['correct_count'],
                      result['total']-result['correct_count'],result['time_spent']))
        conn.execute('UPDATE learning_attempts SET result=%s::jsonb,submitted_at=CURRENT_TIMESTAMP WHERE id=%s',
                     (json.dumps(result,ensure_ascii=False),attempt_id))
    return result


def _check(record, student_id, kind, scope):
    if not record or record['student_id'] != int(student_id) or record['kind'] != kind or record['scope'] != str(scope):
        raise AttemptError('Intento no válido para este alumno y actividad.')
    if record.get('result') and record['result'].get('expired'):
        raise AttemptError('Este intento fue cerrado por el profesor. Vuelve a abrir la evaluación.')


def reopen_exam(student_id, assessment_id, teacher_id):
    if Config.USE_MOCK_DATA:
        with _lock:
            used = [a for a in _attempts.values() if a['student_id']==int(student_id) and a['assessment_id']==assessment_id]
            for a in used:
                if a['result'] is None:
                    a['result'] = {'expired': True}
            _permissions[(int(student_id),assessment_id)] = len(used) + 1
        return
    with _database() as conn:
        _exam_lock(conn,student_id,assessment_id)
        conn.execute("UPDATE learning_attempts SET result='{\"expired\":true}'::jsonb,submitted_at=CURRENT_TIMESTAMP "
                     "WHERE student_id=%s AND assessment_id=%s AND kind='exam' AND result IS NULL",(student_id,assessment_id))
        count = conn.execute("SELECT COUNT(*) AS n FROM learning_attempts WHERE student_id=%s AND assessment_id=%s AND kind='exam'",
                             (student_id,assessment_id)).fetchone()['n']
        legacy = conn.execute('SELECT COUNT(*) AS n FROM student_assessment_attempts WHERE student_id=%s AND assessment_id=%s',
                              (student_id,assessment_id)).fetchone()['n']
        conn.execute('INSERT INTO exam_permissions (student_id,assessment_id,allowed_attempts,reopened_by,reopened_at) '
                     'VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP) ON CONFLICT (student_id,assessment_id) DO UPDATE '
                     'SET allowed_attempts=EXCLUDED.allowed_attempts,reopened_by=EXCLUDED.reopened_by,reopened_at=EXCLUDED.reopened_at',
                     (student_id,assessment_id,max(count,legacy)+1,teacher_id))
