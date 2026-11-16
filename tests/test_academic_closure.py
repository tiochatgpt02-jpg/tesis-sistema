from services import academic_closure_service as closure, academic_calendar_service as calendar
from services import grading_policy_service as policy, bimester_grade_service as grades, db_service
from tests.test_bimester_gradebook import POLICY
import pytest


def test_closed_period_freezes_scores_weights_and_rejects_changes(monkeypatch):
    students = [{'id':1,'grade':5,'first_name':'Prueba','last_name':''}]
    monkeypatch.setattr(db_service, 'fetch_students', lambda: students)
    monkeypatch.setattr(db_service, 'fetch_student_by_id', lambda identity: students[0])
    monkeypatch.setattr(db_service, 'fetch_student_results', lambda **kwargs: [])
    monkeypatch.setattr(grades, '_manual', {})
    monkeypatch.setattr(grades, '_sources', {})
    monkeypatch.setattr(policy, '_policy', POLICY)
    monkeypatch.setattr(grades, 'source_options', lambda grade: [])
    with pytest.raises(ValueError, match='calendario'):
        closure.change_closure(5, 2026, 4, 'close', 'Cierre de prueba', 1)
    periods = [dict(date_from=f'2026-{month:02d}-01',date_to=f'2026-{month+1:02d}-28') for month in (3,5,7,9)]
    calendar.save_calendar(2026, periods, True, 1)
    grades.save_marks(1,2026,4,{'homework':10,'participation':12,'book':14},1)
    result = closure.change_closure(5,2026,4,'close','Cierre de prueba',1)
    assert result['closed'] is True
    assert result['snapshot']['scores']['1']['homework'] == 10
    assert result['snapshot']['scores']['1']['exam'] is None
    for action in (lambda: grades.save_marks(1,2026,4,{'homework':20},1),
                   lambda: grades.save_sources(5,2026,4,{},1)):
        with pytest.raises(ValueError, match='cerrado'):
            action()
    policy.save_component_policy({'homework':5,'participation':10,'book':10,'practice_1':10,'practice_2':10,'exam':55})
    marks, _ = grades.component_results(students,[],2026,4)
    summary = policy.component_summary(marks,policy.get_policy())
    assert summary['weights']['homework'] == 10 and summary['scores']['homework'] == 10
    assert summary['average'] is None
    closure.change_closure(5,2026,4,'reopen','Recuperación autorizada',1)
    grades.save_marks(1,2026,4,{'homework':20},1)
    assert grades.grade_rows(students,[],2026,4,policy.get_policy())[0]['scores']['homework'] == 20
    assert [row['action'] for row in closure._events] == ['close','reopen']
