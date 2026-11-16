import pytest
from app import app
from services import literal_history_service as history


def record(student_id=1, period=1):
    return {'student_id': student_id, 'academic_year': 2026, 'period': period, 'grade': 4,
            'ratings': dict(zip(dict(history.DIMENSIONS), ['A','B','B','AD','B'])),
            'final_rating': 'B', 'source_row': 12, 'source_name': 'test.xlsx', 'source_sha256': 'a' * 64}


def test_final_literal_uses_supplied_modal_rule_and_first_tie_without_numeric_conversion():
    assert history.modal_rating(['A','B','B','AD','B']) == 'B'
    assert history.modal_rating(['AD','A','AD','A','C']) == 'AD'
    assert history.modal_rating(['A','AD','AD','A','C']) == 'A'
    with pytest.raises(ValueError):
        history.modal_rating(['A', 'B', 12, 'C', 'AD'])


def test_name_matching_handles_surname_order_accents_and_preserves_enye():
    assert history.name_key('Pérez Gómez, Ana María') == history.name_key('Ana Maria Perez Gomez')
    assert history.name_key('Ana Niño') != history.name_key('Ana Nino')
    parsed = {'records': [{'name': 'Pérez Gómez, Ana María', 'source_row': 12, 'academic_year': 2026,
                           'period': 1, 'grade': 4, 'ratings': record()['ratings'], 'final_rating': 'B'}],
              'source_sha256': 'a' * 64, 'source_name': 'test.xlsx'}
    students = [{'id': 7, 'grade': 4, 'first_name': 'Ana María', 'last_name': 'Pérez Gómez'}]
    prepared = history.prepare_import(parsed, students)
    assert prepared[0]['student_id'] == 7 and prepared[0]['final_rating'] == 'B'
    assert 'name' not in prepared[0] and 'score' not in prepared[0]
    with pytest.raises(ValueError):
        history.prepare_import(parsed, students + [{**students[0], 'id': 8}])
    with pytest.raises(ValueError):
        history.prepare_import(parsed, [{**students[0], 'grade': 5}])


def test_single_period_cannot_claim_institutional_predictive_validation():
    status = history.readiness([record(1), record(2)])
    assert status['status'] == 'INSUFFICIENT_LONGITUDINAL_HISTORY'
    assert status['students_with_later_period'] == 0
    assert status['model_trained'] is False
    later = history.readiness([record(1), record(1, 2)])
    assert later['students_with_later_period'] == 1
    assert later['status'] == 'REQUIRES_TRAINING_VALIDATION'
    assert later['model_trained'] is False


def test_student_literal_history_is_scoped_and_hides_provenance(monkeypatch):
    monkeypatch.setattr(history, '_records', [record(1), record(2)])
    with app.test_client() as client:
        assert client.get('/student/api/institutional-history').status_code == 403
        with client.session_transaction() as session:
            session.update(is_authenticated=True, user_role='student', user='student', student_id=1)
        response = client.get('/student/api/institutional-history')
        assert response.status_code == 200
        rows = response.get_json()['records']
        assert len(rows) == 1 and rows[0]['final_rating'] == 'B'
        assert 'source_sha256' not in rows[0] and 'student_id' not in rows[0]
        assert client.get('/student/api/institutional-history?student_id=2').status_code == 403
        assert client.get('/teacher/api/institutional-history/status').status_code in (302, 401, 403)
