from copy import deepcopy
from datetime import datetime

import pytest
from openpyxl import load_workbook

from app import app
from services import bimester_grade_service as grades
from services import db_service, grading_policy_service as policies
from services.teacher_export_service import build_excel_workbook
from services.teacher_reports_service import build_academic_report


POLICY = {'mode': 'components', 'weights': {'homework': 10, 'participation': 10, 'book': 10, 'practice_1': 10, 'practice_2': 10, 'exam': 50}}
SCORES = dict(zip(POLICY['weights'], [10, 12, 14, 16, 18, 20]))
STUDENTS = [{'id': 1, 'grade': 5, 'first_name': 'Alumno de prueba', 'last_name': '', 'section': ''},
            {'id': 2, 'grade': 4, 'first_name': 'Otro alumno', 'last_name': '', 'section': ''}]


@pytest.fixture(autouse=True)
def gradebook(monkeypatch):
    monkeypatch.setattr(grades, '_manual', {})
    monkeypatch.setattr(grades, '_sources', {})
    monkeypatch.setattr(policies, '_policy', deepcopy(POLICY))
    monkeypatch.setattr(db_service, 'fetch_students', lambda: deepcopy(STUDENTS))
    monkeypatch.setattr(db_service, 'fetch_student_by_id', lambda identity: next((deepcopy(row) for row in STUDENTS if row['id'] == int(identity)), None))
    monkeypatch.setattr(db_service, 'fetch_student_results', lambda **kwargs: [])
    monkeypatch.setattr(grades, 'source_options', lambda grade: [
        {'value': 'practice:material:12', 'kind': 'practice', 'label': 'Práctica de prueba'},
        {'value': 'practice:material:13', 'kind': 'practice', 'label': 'Otra práctica'},
        {'value': 'exam:4', 'kind': 'exam', 'label': 'Examen de prueba'},
    ])


def notes(scores=SCORES):
    return [{'student_id': 1, 'grade_component': key, 'score': score, 'activity_type': 'component'} for key, score in scores.items()]


def test_six_weights_apply_exam_50_and_five_components_10():
    assert policies.save_component_policy(POLICY['weights']) == POLICY
    assert policies.academic_average(notes(), POLICY) == 17
    assert policies.component_summary(notes(), POLICY)['missing'] == []


def test_missing_grade_is_pending_but_zero_is_a_real_grade():
    assert policies.academic_average(notes({key: 20 for key in SCORES if key != 'exam'}), POLICY) is None
    assert policies.academic_average(notes({key: (0 if key == 'exam' else 20) for key in SCORES}), POLICY) == 10
    assert policies.academic_average(notes({key: 0 for key in SCORES}), POLICY) == 0


@pytest.mark.parametrize('change', [ {'exam': 40}, {'homework': -10, 'exam': 70},
                                    {'homework': '10.5'}, {'exam': True}, {'homework': 50, 'exam': 10} ])
def test_invalid_percentages_are_rejected_without_changing_policy(change):
    with pytest.raises(ValueError):
        policies.save_component_policy({**POLICY['weights'], **change})
    assert policies.get_policy() == POLICY


def test_games_and_untagged_results_do_not_enter_component_average():
    extra = [{'student_id': 1, 'grade_component': 'exam', 'score': 0, 'activity_type': 'juegos', 'id': 99},
             {'student_id': 1, 'score': 0, 'activity_type': 'evaluaciones', 'item_type': 'exam:999'}]
    assert policies.academic_average(notes() + extra, POLICY) == 17


def test_manual_marks_preserve_year_period_student_and_validate_atomically():
    grades.save_marks(1, 2026, 4, SCORES, 1)
    grades.save_marks(1, 2026, 3, {'exam': 0}, 1)
    grades.save_marks(2, 2026, 4, {'exam': 8}, 1)
    assert grades.grade_rows([STUDENTS[0]], [], 2026, 4, POLICY)[0]['average'] == 17
    assert grades.grade_rows([STUDENTS[0]], [], 2027, 4, POLICY)[0]['average'] is None
    before = deepcopy(grades._manual)
    for value in ('NaN', 'Infinity', True, -1, 21, '1.001'):
        with pytest.raises(ValueError):
            grades.save_marks(1, 2026, 4, {'homework': 19, 'exam': value}, 1)
        assert grades._manual == before
    grades.save_marks(1, 2026, 4, {'exam': ''}, 1)
    summary = grades.grade_rows([STUDENTS[0]], [], 2026, 4, POLICY)[0]
    assert summary['average'] is None and summary['scores']['exam'] is None
    assert grades.grade_rows([STUDENTS[1]], [], 2026, 4, POLICY)[0]['scores']['exam'] == 8


def test_linked_practice_uses_latest_in_term_and_cannot_be_overwritten_manually():
    grades.save_marks(1, 2026, 4, SCORES, 1)
    grades.save_sources(5, 2026, 4, {'practice_1': 'practice:material:12'}, 1)
    results = [dict(student_id=1, item_type='practice:material:12', score=4, created_at='2026-11-01', id=1),
               dict(student_id=1, item_type='practice:material:12', score=20, created_at='2026-11-02', id=2),
               dict(student_id=1, item_type='practice:material:12', score=0, created_at='2027-11-03', id=3),
               dict(student_id=2, item_type='practice:material:12', score=0, created_at='2026-11-03', id=4)]
    row = grades.grade_rows([STUDENTS[0]], results, 2026, 4, POLICY)[0]
    assert row['scores']['practice_1'] == 20
    assert row['average'] == 17.4
    assert grades.grade_rows([STUDENTS[0]], [], 2026, 4, POLICY)[0]['average'] is None
    with pytest.raises(ValueError):
        grades.save_marks(1, 2026, 4, {'practice_1': 5}, 1)
    with pytest.raises(ValueError):
        grades.save_sources(5, 2026, 4, {'practice_1': 'practice:material:12', 'practice_2': 'practice:material:12'}, 1)
    with pytest.raises(ValueError):
        grades.save_sources(5, 2026, 4, {'exam': 'practice:material:12'}, 1)


def test_report_and_excel_have_same_six_component_average_and_period():
    year = datetime.now().year
    grades.save_marks(1, year, 4, SCORES, 1)
    results = grades.with_component_results(STUDENTS, [], POLICY, 4, year)
    report = build_academic_report(STUDENTS, results, grade=5, period='4', policy=POLICY)
    assert report['rows'][0]['average'] == 17
    assert report['rows'][0]['components'] == SCORES
    assert report['rows'][0]['section'] == ''
    other = build_academic_report(STUDENTS, results, grade=5, period='3', policy=POLICY)
    assert other['rows'][0]['average'] is None
    workbook = load_workbook(build_excel_workbook(STUDENTS, results, grade=5, period='4', policy=POLICY))
    sheet = workbook.active
    assert sheet.max_column == 12
    assert sheet['J4'].value == 'Examen bimestral'
    assert sheet['J5'].value == 20
    assert sheet['K5'].value == 17


def teacher(client):
    with client.session_transaction() as session:
        session.update(is_authenticated=True, user_role='teacher', user='docente', user_id=1)


def test_teacher_can_save_six_marks_and_student_cannot_modify_gradebook():
    year = datetime.now().year
    with app.test_client() as client:
        assert client.get('/teacher/bimester-grades').status_code in (302, 401, 403)
        teacher(client)
        response = client.get(f'/teacher/bimester-grades?grade=5&year={year}&period=4')
        assert response.status_code == 200
        with client.session_transaction() as session:
            token = session['gradebook_csrf']
        form = {'action': 'marks', 'grade': 5, 'year': year, 'period': 4, 'student_id': 1, **SCORES}
        assert client.post('/teacher/bimester-grades', data=form).status_code == 403
        form['csrf_token'] = token
        assert client.post('/teacher/bimester-grades', data=form).status_code == 303
        report = client.get('/teacher/api/reports/gradebook?grade=5&period=4').get_json()
        assert report['rows'][0]['average'] == 17
        assert client.post('/teacher/bimester-grades', data={**form, 'student_id': 2}).status_code == 400
        with client.session_transaction() as session:
            session['user_role'] = 'student'
        before = deepcopy(grades._manual)
        assert client.post('/teacher/bimester-grades', data={**form, 'exam': 0}).status_code in (302, 403)
        assert grades._manual == before


def test_settings_accept_six_weights_and_explain_invalid_total():
    with app.test_client() as client:
        teacher(client)
        response = client.post('/teacher/settings', data=POLICY['weights'])
        assert response.status_code == 200
        assert policies.get_policy() == POLICY
        response = client.post('/teacher/settings', data={**POLICY['weights'], 'exam': 40})
        assert response.status_code == 400
        assert 'sumar 100' in response.get_data(as_text=True)


def test_student_progress_uses_current_bimester_weighted_marks(monkeypatch):
    from services.student_learning_service import build_student_progress
    year, period = grades.current_term()
    grades.save_marks(1, year, period, SCORES, 1)
    monkeypatch.setattr(db_service, 'fetch_student_progress', lambda identity: {})
    monkeypatch.setattr(db_service, 'fetch_student_activity_summary', lambda identity: {})
    monkeypatch.setattr(db_service, 'fetch_topic_progress', lambda identity: [])
    progress = build_student_progress(1, [])
    assert progress['average_grade'] == 17
    assert progress['average_status'] == 'weighted'
