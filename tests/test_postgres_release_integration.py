"""Opt-in verification against PostgreSQL, isolated from school tables."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest

from config import Config
from services import db_service
from services.learning_attempt_service import start_attempt, submit_attempt, reopen_exam, AttemptError


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requires TEST_DATABASE_URL for an isolated PostgreSQL schema')
def test_persisted_exam_is_atomic_idempotent_and_reopens_without_losing_history(monkeypatch):
    url=os.environ['TEST_DATABASE_URL']
    schema='release_test_'+uuid4().hex
    root=Path(__file__).resolve().parents[1]
    with psycopg.connect(url,autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    def connect():
        # Neon pooled URLs reject search_path as a startup parameter. SET LOCAL
        # keeps the schema scoped to this transaction on the pooled connection.
        connection=psycopg.connect(url,row_factory=dict_row,connect_timeout=10)
        connection.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        return connection
    try:
        with connect() as conn:
            conn.execute((root/'sql/postgresql/ddl.sql').read_text(encoding='utf-8'))
            for migration in sorted((root/'sql/migrations/postgresql').glob('*.sql')):
                conn.execute(migration.read_text(encoding='utf-8'))
            sid=conn.execute("INSERT INTO students (first_name,grade) VALUES ('Test',5) RETURNING id").fetchone()['id']
            tid=conn.execute("INSERT INTO topics (title,grade,status) VALUES ('Word',5,'Publicado') RETURNING id").fetchone()['id']
            uid=conn.execute("INSERT INTO users (username,password_hash,role) VALUES ('test_teacher','unused','teacher') RETURNING id").fetchone()['id']
            aid=conn.execute("INSERT INTO assessment (topic_id,title,status) VALUES (%s,'Test','PUBLISHED') RETURNING id",(tid,)).fetchone()['id']
        monkeypatch.setattr(Config,'USE_MOCK_DATA',False)
        monkeypatch.setattr(db_service,'get_connection',connect)
        questions=[{'question':'Herramienta para texto','options':['Word','Excel'],'answer':'Word'}]
        attempt=start_attempt(sid,tid,'exam',str(aid),questions,aid)
        result=submit_attempt(attempt['id'],sid,'exam',str(aid),{'0':'Word'})
        assert result['score']==20
        assert submit_attempt(attempt['id'],sid,'exam',str(aid),{'0':'Excel'})==result
        with connect() as conn:
            assert conn.execute('SELECT COUNT(*) AS n FROM student_notes').fetchone()['n']==1
            assert conn.execute('SELECT COUNT(*) AS n FROM student_assessment_attempts').fetchone()['n']==1
        with pytest.raises(AttemptError):
            start_attempt(sid,tid,'exam',str(aid),questions,aid)
        reopen_exam(sid,aid,uid)
        second=start_attempt(sid,tid,'exam',str(aid),questions,aid)
        assert second['id']!=attempt['id']
        assert submit_attempt(second['id'],sid,'exam',str(aid),{'0':'Excel'})['score']==0
        with connect() as conn:
            assert conn.execute('SELECT COUNT(*) AS n FROM student_assessment_attempts').fetchone()['n']==2
            assert conn.execute('SELECT reopened_by FROM exam_permissions').fetchone()['reopened_by']==uid

        # Exercise the actual Flask endpoints against this PostgreSQL schema.
        from app import app
        from services.practice_service import save_practice
        from services.grading_policy_service import academic_average
        material_text='Word permite crear documentos. Excel permite trabajar con hojas de calculo.'
        practice_questions=[
            {'question':'Herramienta para documentos','options':['Word','Excel'],'answer':'Word'},
            {'question':'Herramienta para hojas de calculo','options':['Word','Excel'],'answer':'Excel'},
        ]
        with connect() as conn:
            mid=conn.execute("INSERT INTO learning_materials (topic_id,title,material_type,content,status) "
                             "VALUES (%s,'Herramientas','texto',%s,'PUBLISHED') RETURNING id",(tid,material_text)).fetchone()['id']
        save_practice(f'material:{mid}',material_text,5,{'questions':practice_questions,'source':'simulation_fixture'})
        game_id=db_service.create_ai_generated_game(
            topic_id=tid,material_id=mid,presentation_id=None,game_type='multiple_choice',
            title='Entrenamiento de Word',instruction='Elige la herramienta de documentos.',
            content_json={'question':'Herramienta para documentos','options':['Word','Excel'],'answer':'Word'},
            status='PUBLISHED',created_by=uid)
        with app.test_client() as client:
            with client.session_transaction() as session:
                session.update(user='simulation_student',user_role='student',student_id=sid,
                               user_grade=5,user_section='A',is_authenticated=True)
            response=client.get(f'/student/api/materials/{mid}/practice')
            assert response.status_code==200
            practice=response.get_json()
            assert all('answer' not in q for q in practice['questions'])
            response=client.post(f'/student/api/materials/{mid}/practice',json={
                'attempt_id':practice['attempt_id'],'answers':{'0':'Word','1':'Word'}})
            assert response.status_code==200
            assert response.get_json()['score']==10
            # Six retries over separate real connections must preserve one note.
            with ThreadPoolExecutor(max_workers=6) as pool:
                retries=list(pool.map(lambda _:submit_attempt(practice['attempt_id'],sid,'practice',f'material:{mid}',
                                                               {'0':'Word','1':'Excel'}),range(6)))
            assert all(r['score']==10 for r in retries)
            with connect() as conn:
                assert conn.execute('SELECT COUNT(*) AS n FROM student_notes').fetchone()['n']==3
            repeated=client.get(f'/student/api/materials/{mid}/practice').get_json()
            assert repeated['attempt_id']!=practice['attempt_id']
            response=client.post(f'/student/api/materials/{mid}/practice',json={
                'attempt_id':repeated['attempt_id'],'answers':{'0':'Word','1':'Excel'}})
            assert response.status_code==200
            assert response.get_json()['score']==20
            for _ in range(3):
                response=client.post(f'/student/api/ai-games/{game_id}/play',json={'answer':'Word','time_spent':3})
                assert response.status_code==200
                assert response.get_json()['is_correct'] is True
        with connect() as conn:
            assert conn.execute('SELECT COUNT(*) AS n FROM student_notes').fetchone()['n']==4
            assert conn.execute('SELECT COUNT(*) AS n FROM student_game_attempts').fetchone()['n']==3
        # Example weights belong only to this temporary simulation.
        notes=db_service.fetch_student_results(student_id=sid)
        assert academic_average(notes,{'practice_weight':30,'exam_weight':70})==6
        from services.file_storage_service import store_bytes, read_bytes
        monkeypatch.setattr(Config,'DATABASE_URL',url)
        store_bytes('presentations/test.txt',b'Contenido docente')
        assert read_bytes('presentations/test.txt')==b'Contenido docente'
    finally:
        with psycopg.connect(url,autocommit=True) as admin:
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
