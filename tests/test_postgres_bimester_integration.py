"""Optional real persistence check, isolated from the school's schema."""
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest

from config import Config
from services import db_service, bimester_grade_service as grades, grading_policy_service as policies


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requires an isolated PostgreSQL test connection')
def test_six_component_gradebook_persists_and_links_real_results(monkeypatch):
    url = os.environ['TEST_DATABASE_URL']
    schema = 'gradebook_test_' + uuid4().hex
    root = Path(__file__).resolve().parents[1]
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))

    def connect():
        connection = psycopg.connect(url, row_factory=dict_row, connect_timeout=10)
        connection.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        return connection

    try:
        with connect() as connection:
            connection.execute((root / 'sql/postgresql/ddl.sql').read_text(encoding='utf-8'))
            for migration in sorted((root / 'sql/migrations/postgresql').glob('*.sql')):
                connection.execute(migration.read_text(encoding='utf-8'))
            # Reapply the migration to verify that a redeploy preserves grades.
            connection.execute((root / 'sql/migrations/postgresql/20261114_grading_components.sql').read_text(encoding='utf-8'))
            sid = connection.execute("INSERT INTO students(first_name,grade,section) VALUES ('Prueba',5,'') RETURNING id").fetchone()['id']
            uid = connection.execute("INSERT INTO users(username,password_hash,role) VALUES ('teacher_test','unused','teacher') RETURNING id").fetchone()['id']
            topic = connection.execute("INSERT INTO topics(title,grade) VALUES ('Tema de prueba',5) RETURNING id").fetchone()['id']
            material = connection.execute("INSERT INTO learning_materials(topic_id,title,material_type) VALUES (%s,'Material de prueba','texto') RETURNING id", (topic,)).fetchone()['id']
            material2 = connection.execute("INSERT INTO learning_materials(topic_id,title,material_type) VALUES (%s,'Segunda práctica','texto') RETURNING id", (topic,)).fetchone()['id']
            exam = connection.execute("INSERT INTO assessment(topic_id,title) VALUES (%s,'Examen de prueba') RETURNING id", (topic,)).fetchone()['id']
        monkeypatch.setattr(Config, 'USE_MOCK_DATA', False)
        monkeypatch.setattr(db_service, 'get_connection', connect)
        policy = policies.get_policy()
        assert policy['weights'] == {'homework': 10, 'participation': 10, 'book': 10, 'practice_1': 10, 'practice_2': 10, 'exam': 50}
        scores = dict(zip(policy['weights'], [10, 12, 14, 16, 18, 20]))
        grades.save_marks(sid, 2026, 4, {key: scores[key] for key in ('homework', 'participation', 'book')}, uid)
        with connect() as connection:
            connection.execute((root / 'sql/migrations/postgresql/20261114_grading_components.sql').read_text(encoding='utf-8'))
            assert connection.execute('SELECT COUNT(*) AS n FROM bimester_manual_grades').fetchone()['n'] == 3
        students = [db_service.fetch_student_by_id(sid)]
        assert grades.grade_rows(students, [], 2026, 4, policy)[0]['average'] is None
        grades.save_sources(5, 2026, 4, {'practice_1': f'practice:material:{material}',
                           'practice_2': f'practice:material:{material2}', 'exam': f'exam:{exam}'}, uid)
        db_service.record_student_result(sid, topic, 'actividades', f'practice:material:{material}', 16, created_at='2026-11-09 10:00:00')
        db_service.record_student_result(sid, topic, 'actividades', f'practice:material:{material2}', 18, created_at='2026-11-09 11:00:00')
        db_service.record_student_result(sid, topic, 'evaluaciones', f'exam:{exam}', 20, created_at='2026-11-09 12:00:00')
        assert grades.grade_rows(students, db_service.fetch_student_results(student_id=sid), 2026, 4, policy)[0]['average'] == 17
        db_service.record_student_result(sid, topic, 'actividades', f'practice:material:{material}', 20, created_at='2026-11-10 10:00:00')
        db_service.record_student_result(sid, topic, 'evaluaciones', f'exam:{exam}', 0, created_at='2026-11-10 11:00:00')
        rows = grades.grade_rows(students, db_service.fetch_student_results(student_id=sid), 2026, 4, policy)
        assert rows[0]['scores']['practice_1'] == 20
        assert rows[0]['scores']['exam'] == 0
        assert rows[0]['average'] == 7.4
        assert grades.grade_rows(students, [], 2026, 3, policy)[0]['average'] is None
        with pytest.raises(ValueError):
            grades.save_marks(sid, 2026, 4, {'exam': 15}, uid)
    finally:
        with psycopg.connect(url, autocommit=True) as admin:
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
