from datetime import date
import pytest
from app import app
from services import academic_calendar_service as calendar
from services.teacher_reports_service import period_date_range


@pytest.fixture(autouse=True)
def isolated_calendar(monkeypatch):
    monkeypatch.setattr(calendar, '_calendars', {})
    monkeypatch.setattr(calendar, '_bounds', {})


PERIODS = [
    {'date_from': '2026-03-20', 'date_to': '2026-05-15'},
    {'date_from': '2026-05-18', 'date_to': '2026-07-17'},
    {'date_from': '2026-08-03', 'date_to': '2026-10-02'},
    {'date_from': '2026-10-05', 'date_to': '2026-12-18'},
]


def test_calendar_is_provisional_until_teacher_confirms():
    assert calendar.get_calendar(2026)['confirmed'] is False
    result = calendar.save_calendar(2026, PERIODS, True, 1)
    assert result['confirmed'] is True
    assert period_date_range('2', 2026) == ('2026-05-18', '2026-07-17', 'Bimestre 2')


def test_2026_reference_is_editable_and_never_confirmed_automatically():
    result=calendar.get_calendar(2026)
    assert result['confirmed'] is False
    assert [(str(row['date_from']),str(row['date_to'])) for row in result['periods']] == [
        ('2026-03-20','2026-05-15'),('2026-05-25','2026-07-24'),
        ('2026-08-10','2026-10-09'),('2026-10-19','2026-12-18')]
    assert result['reference_source'] == calendar.REFERENCE_SOURCE
    edited=calendar.save_calendar(2026,PERIODS,False,1)
    assert edited['reference_source'] is None and edited['confirmed'] is False
    assert period_date_range(2,2026)[:2] == ('2026-05-18','2026-07-17')


def test_calendar_filters_report_and_current_term_from_same_dates(monkeypatch):
    calendar.save_calendar(2026, PERIODS, True, 1)
    monkeypatch.setattr(calendar, 'school_today', lambda: date(2026, 10, 7))
    assert calendar.current_term() == (2026, 4)
    assert period_date_range(4, 2026)[:2] == ('2026-10-05', '2026-12-18')


@pytest.mark.parametrize('periods', [PERIODS[:3],
    [PERIODS[0], {**PERIODS[1], 'date_from': '2026-05-14'}, *PERIODS[2:]],
    [{**PERIODS[0], 'date_to': '2025-05-01'}, *PERIODS[1:]],
    [{**PERIODS[0], 'date_from': 'bad date'}, *PERIODS[1:]],
])
def test_invalid_calendars_do_not_replace_saved_dates(periods):
    calendar.save_calendar(2026, PERIODS, True, 1)
    with pytest.raises(ValueError):
        calendar.save_calendar(2026, periods, True, 1)
    assert period_date_range(1, 2026)[:2] == ('2026-03-20', '2026-05-15')


def test_bimesters_must_fit_supplied_school_year_bounds():
    calendar._bounds[2026] = {'date_from': date(2026, 3, 20), 'date_to': date(2026, 12, 18), 'source': 'Test'}
    assert calendar.get_calendar(2026)['periods'][0]['date_from'] == date(2026, 3, 20)
    with pytest.raises(ValueError):
        calendar.save_calendar(2026, [{**PERIODS[0], 'date_from': '2026-03-01'}, *PERIODS[1:]], True, 1)


def test_calendar_requires_teacher_and_csrf():
    with app.test_client() as client:
        assert client.get('/teacher/academic-calendar').status_code in (302, 401, 403)
        with client.session_transaction() as session:
            session.update(user_role='teacher', is_authenticated=True, user='teacher', user_id=1)
        assert client.get('/teacher/academic-calendar?year=2026').status_code == 200
        data = {'year': 2026, 'confirmed': 'yes'}
        for index, period in enumerate(PERIODS, 1):
            data[f'start_{index}'], data[f'end_{index}'] = period['date_from'], period['date_to']
        assert client.post('/teacher/academic-calendar', data=data).status_code == 403
        with client.session_transaction() as session:
            data['csrf_token'] = session['calendar_csrf']
        assert client.post('/teacher/academic-calendar', data=data).status_code == 303
        assert calendar.get_calendar(2026)['confirmed'] is True
