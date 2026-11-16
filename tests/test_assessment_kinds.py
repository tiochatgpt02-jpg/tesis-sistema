import pytest
from app import app
from services import db_service
from services.learning_attempt_service import _attempts


@pytest.fixture
def assessments(monkeypatch):
    monkeypatch.setattr(db_service, 'fetch_topic_by_id', lambda identity: {'id': int(identity), 'grade': 5, 'status': 'Publicado', 'section': ''})
    result = []
    for kind, title in [('practice','Práctica 1'), ('practice','Práctica 2'), ('exam','Examen bimestral')]:
        identity = db_service.create_assessment(100, title, 1, 'PUBLISHED', kind=kind)
        db_service.create_question(identity, '¿Qué programa sirve para escribir?', 'Word', 'Paint', 'Excel', 'Word', approved=True)
        result.append(identity)
    return result


def student(client, grade=5):
    with client.session_transaction() as session:
        session.update(user='student', user_role='student', is_authenticated=True, student_id=1, user_grade=grade, user_section='')


def test_preview_lists_two_practices_and_exam_without_starting_clock(assessments):
    with app.test_client() as client:
        student(client)
        listed = client.get('/student/api/topics/100/assessments').get_json()['assessments']
        assert {row['id'] for row in listed} == set(assessments)
        assert sum(row['kind'] == 'practice' for row in listed) == 2
        assert db_service.fetch_published_assessment_for_topic(100)['id'] == assessments[2]
        preview = client.get(f'/student/api/assessments/{assessments[2]}').get_json()['assessment']
        assert preview['duration_minutes'] == 30
        assert 'questions' not in preview and len(_attempts) == 0


def test_practice_repeats_and_writes_identified_automatic_marks(assessments, monkeypatch):
    identity = assessments[0]
    with app.test_client() as client:
        student(client)
        first = client.post(f'/student/api/assessments/{identity}/start').get_json()
        assert {'answer', 'correct_answer'}.isdisjoint(first['attempt']['questions'][0])
        correct = client.post(f'/student/api/assessments/{identity}/attempt', json={'attempt_id':first['attempt']['attempt_id'],'answers':{'0':'Word'}})
        assert correct.get_json()['result']['score'] == 20
        second = client.post(f'/student/api/assessments/{identity}/start').get_json()
        assert second['attempt']['attempt_id'] != first['attempt']['attempt_id']
        wrong = client.post(f'/student/api/assessments/{identity}/attempt', json={'attempt_id':second['attempt']['attempt_id'],'answers':{'0':'Paint'}})
        assert wrong.get_json()['result']['score'] == 0
        notes = [row for row in db_service.fetch_student_results(student_id=1) if row.get('item_type') == f'practice:{identity}']
        assert [row['score'] for row in notes] == [20, 0]
        from services import bimester_grade_service as grades
        year, period = grades.current_term()
        monkeypatch.setattr(grades, 'source_options', lambda grade: [{'value':f'practice:{identity}', 'kind':'practice'}])
        grades.save_sources(5,year,period,{'practice_1':f'practice:{identity}'},1)
        marks, _ = grades.component_results([{'id':1,'grade':5}], notes, year, period)
        assert [(row['grade_component'],row['score']) for row in marks] == [('practice_1',0)]


def test_exam_has_one_attempt_and_teacher_can_reopen(assessments):
    identity = assessments[2]
    with app.test_client() as client:
        student(client)
        start = client.post(f'/student/api/assessments/{identity}/start').get_json()
        assert start['remaining_seconds'] >= 1798
        assert client.post(f'/student/api/assessments/{identity}/attempt', json={'attempt_id':start['attempt']['attempt_id'],'answers':{'0':'Word'}}).get_json()['result']['score'] == 20
        assert client.post(f'/student/api/assessments/{identity}/start').status_code == 409
        with client.session_transaction() as session:
            session.update(user_role='teacher', user_id=1)
        assert client.post(f'/teacher/api/assessments/{identity}/students/1/reopen').status_code == 200
        student(client)
        assert client.post(f'/student/api/assessments/{identity}/start').status_code == 200


def test_wrong_grade_is_denied_and_frozen_attempt_survives_question_edit(assessments):
    identity = assessments[2]
    with app.test_client() as client:
        student(client, 6)
        assert client.post(f'/student/api/assessments/{identity}/start').status_code == 404
        student(client)
        start = client.post(f'/student/api/assessments/{identity}/start').get_json()
        question = db_service.fetch_assessment_by_id(identity)['questions'][0]
        with client.session_transaction() as session:
            session.update(user_role='teacher', user_id=1)
        changed = client.put(f'/teacher/api/assessments/{identity}/questions/{question["id"]}', json={'answer':'Paint'})
        assert changed.status_code == 200
        assert db_service.fetch_assessment_by_id(identity)['status'] == 'PENDING_REVIEW'
        assert client.put(f'/teacher/api/assessments/{assessments[0]}/questions/{question["id"]}', json={'answer':'Paint'}).status_code == 404
        student(client)
        assert client.post(f'/student/api/assessments/{identity}/start').status_code == 404
        saved = client.post(f'/student/api/assessments/{identity}/attempt', json={'attempt_id':start['attempt']['attempt_id'],'answers':{'0':'Word'}})
        assert saved.get_json()['result']['score'] == 20
