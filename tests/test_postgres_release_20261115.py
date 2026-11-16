"""Real PostgreSQL verification in a disposable schema, never the school tables."""
import os
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest
from app import app
from config import Config
from services import db_service, literal_history_service as history
from services import grading_policy_service as policies, bimester_grade_service as grades
from services import academic_calendar_service as calendar, academic_closure_service as closure


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requires explicitly authorized isolated PostgreSQL testing')
def test_real_literal_history_auto_assessments_and_frozen_closure(monkeypatch):
    url = os.environ['TEST_DATABASE_URL']
    schema = 'release20261115_' + uuid4().hex
    root = Path(__file__).resolve().parents[1]
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))

    def connect():
        conn = psycopg.connect(url, row_factory=dict_row, connect_timeout=10)
        conn.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        return conn

    try:
        with connect() as conn:
            conn.execute((root/'sql/postgresql/ddl.sql').read_text(encoding='utf-8'))
            migrations = sorted((root/'sql/migrations/postgresql').glob('*.sql'))
            for migration in migrations:
                conn.execute(migration.read_text(encoding='utf-8'))
            for migration in migrations:
                conn.execute(migration.read_text(encoding='utf-8'))
            sid = conn.execute("INSERT INTO students(first_name,grade,section) VALUES('Alumno ficticio',5,'') RETURNING id").fetchone()['id']
            uid = conn.execute("INSERT INTO users(username,password_hash,role) VALUES('teacher_fixture','unused','teacher') RETURNING id").fetchone()['id']
            conn.execute("INSERT INTO users(username,password_hash,role,first_name,grade,student_id) VALUES('student_fixture','unused','student','Alumno ficticio',5,%s)", (sid,))
            topic = conn.execute("INSERT INTO topics(title,grade,status) VALUES('Word',5,'Publicado') RETURNING id").fetchone()['id']
            # Reapplying reference dates must not replace a teacher's edits.
            conn.execute("UPDATE academic_calendar SET date_to='2026-05-14' WHERE academic_year=2026 AND period=1")
            conn.execute((root/'sql/migrations/postgresql/20261116_provisional_calendar.sql').read_text())
            reference = conn.execute('SELECT date_to,confirmed FROM academic_calendar WHERE academic_year=2026 AND period=1').fetchone()
            assert str(reference['date_to']) == '2026-05-14' and reference['confirmed'] is False
        monkeypatch.setattr(Config, 'USE_MOCK_DATA', False)
        monkeypatch.setattr(db_service, 'get_connection', connect)
        ratings = {'comprehension':'A','application':'B','completion':'B','homework':'AD','resolution':'B'}
        record = {'student_id':sid,'academic_year':2026,'period':1,'ratings':ratings,'final_rating':'B',
                  'source_sha256':'a'*64,'source_name':'fixture.xlsx','source_row':12}
        assert history.import_records([record]) == 1
        assert history.import_records([record]) == 0
        assert history.fetch_history(student_id=sid)[0]['ratings'] == ratings
        assert history.readiness()['status'] == 'INSUFFICIENT_LONGITUDINAL_HISTORY'
        with connect() as conn:
            assert conn.execute('SELECT COUNT(*) AS n FROM student_notes').fetchone()['n'] == 0
        ids = []
        for kind in ('practice','practice','exam'):
            identity = db_service.create_assessment(topic, 'Evaluación ficticia', uid, 'PUBLISHED', kind=kind)
            db_service.create_question(identity, '¿Qué programa permite escribir?', 'Word','Paint','Excel','Word',approved=True)
            ids.append(identity)
        options = grades.source_options(5)
        assert any(row['value']==f'practice:{ids[0]}' and row['kind']=='practice' for row in options)
        assert any(row['value']==f'exam:{ids[2]}' and row['kind']=='exam' for row in options)
        grades.save_sources(5,2026,4,{'practice_1':f'practice:{ids[0]}','practice_2':f'practice:{ids[1]}','exam':f'exam:{ids[2]}'},uid)
        grades.save_marks(sid,2026,4,{'homework':10,'participation':12,'book':14},uid)
        # Use current date's term for actual attempt timestamps; explicit calendar
        # dates let this fixture remain deterministic around the supplied school year.
        from datetime import datetime, timezone
        from services.learning_attempt_service import start_attempt, submit_attempt
        for identity, kind in zip(ids, ('practice','practice','exam')):
            questions = db_service.fetch_assessment_by_id(identity)['questions']
            attempt = start_attempt(sid,topic,kind,str(identity),questions,identity)
            assert submit_attempt(str(attempt['id']),sid,kind,str(identity),{'0':'Word'})['score']==20
        with connect() as conn:
            conn.execute("UPDATE student_notes SET created_at='2026-11-10 10:00:00'")
        student = db_service.fetch_student_by_id(sid)
        results = db_service.fetch_student_results(student_id=sid)
        policy = policies.get_policy()
        assert grades.grade_rows([student],results,2026,4,policy)[0]['average'] == 17.6
        with pytest.raises(ValueError):
            grades.save_marks(sid,2026,4,{'exam':0},uid)
        periods = [dict(date_from='2026-03-20',date_to='2026-05-15'),
                   dict(date_from='2026-05-18',date_to='2026-07-17'),
                   dict(date_from='2026-08-03',date_to='2026-10-02'),
                   dict(date_from='2026-10-05',date_to='2026-12-18')]
        calendar.save_calendar(2026,periods,True,uid)
        closed = closure.change_closure(5,2026,4,'close','Cierre ficticio verificado',uid)
        assert closed['snapshot']['scores'][str(sid)]['exam']==20
        with pytest.raises(ValueError, match='cerrado'):
            grades.save_marks(sid,2026,4,{'homework':0},uid)
        policies.save_component_policy({'homework':5,'participation':10,'book':10,'practice_1':10,'practice_2':10,'exam':55})
        assert grades.grade_rows([student],results,2026,4,policies.get_policy())[0]['average']==17.6
        closure.change_closure(5,2026,4,'reopen','Recuperación ficticia',uid)
        assert not closure.closed_periods(2026,4)
        with connect() as conn:
            events = conn.execute('SELECT action FROM bimester_closure_events ORDER BY id').fetchall()
            assert [row['action'] for row in events]==['close','reopen']
            assert conn.execute('SELECT COUNT(*) AS n FROM bimester_manual_grades').fetchone()['n']==3
    finally:
        assert schema.startswith('release20261115_')
        with psycopg.connect(url,autocommit=True) as admin:
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
