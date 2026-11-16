"""School calendar shared by online marks, gradebook and reports."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from flask import g, has_request_context
from config import Config

_calendars = {}
_bounds = {}
DEFAULT_PERIODS = ((3, 1, 5, 31), (6, 1, 7, 31), (8, 1, 10, 31), (11, 1, 12, 31))


def school_today():
    return datetime.now(ZoneInfo('America/Lima')).date()


def validate_year(value):
    try:
        year = int(str(value))
    except (TypeError, ValueError):
        raise ValueError('El año debe estar entre 2000 y 2100.') from None
    if not 2000 <= year <= 2100:
        raise ValueError('El año debe estar entre 2000 y 2100.')
    return year


def get_calendar(year):
    year = validate_year(year)
    cache = g.setdefault('school_calendars', {}) if has_request_context() else {}
    if year in cache:
        return cache[year]
    if Config.USE_MOCK_DATA:
        rows = _calendars.get(year, [])
        bounds = _bounds.get(year)
    else:
        from services.db_service import get_connection
        with get_connection() as conn:
            rows = conn.execute('SELECT period,date_from,date_to,confirmed FROM academic_calendar WHERE academic_year=%s ORDER BY period', (year,)).fetchall()
            bounds = conn.execute('SELECT date_from,date_to,source FROM school_year_bounds WHERE academic_year=%s', (year,)).fetchone()
    if len(rows) != 4:
        rows = [dict(period=index, date_from=date(year, start_month, start_day),
                     date_to=date(year, end_month, end_day), confirmed=False)
                for index, (start_month, start_day, end_month, end_day) in enumerate(DEFAULT_PERIODS, 1)]
        if bounds:
            rows[0]['date_from'] = bounds['date_from']
            rows[-1]['date_to'] = bounds['date_to']
    result = {'year': year, 'periods': [dict(row) for row in rows],
              'confirmed': all(row['confirmed'] for row in rows), 'annual_bounds': dict(bounds) if bounds else None}
    cache[year] = result
    return result


def save_calendar(year, periods, confirmed, teacher_id):
    year = validate_year(year)
    if len(periods) != 4:
        raise ValueError('Debes indicar las fechas de los cuatro bimestres.')
    rows = []
    bounds = get_calendar(year)['annual_bounds']
    for index, item in enumerate(periods, 1):
        try:
            start = date.fromisoformat(str(item['date_from']))
            end = date.fromisoformat(str(item['date_to']))
        except (KeyError, TypeError, ValueError):
            raise ValueError(f'Indica fechas válidas para el bimestre {index}.') from None
        if start.year != year or end.year != year or start > end:
            raise ValueError('Cada bimestre debe comenzar y terminar dentro del año seleccionado y en orden cronológico.')
        if bounds and (start < bounds['date_from'] or end > bounds['date_to']):
            raise ValueError('Los bimestres deben estar dentro del inicio y fin del año escolar indicado.')
        if rows and start <= rows[-1]['date_to']:
            raise ValueError('Los bimestres no deben superponerse y deben estar en orden cronológico.')
        rows.append(dict(period=index, date_from=start, date_to=end, confirmed=bool(confirmed)))
    if Config.USE_MOCK_DATA:
        _calendars[year] = rows
    else:
        from services.db_service import get_connection
        with get_connection() as conn:
            conn.execute('SELECT pg_advisory_xact_lock(%s,%s)', (20261115, year))
            for row in rows:
                conn.execute('INSERT INTO academic_calendar (academic_year,period,date_from,date_to,confirmed,updated_by) '
                             'VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(academic_year,period) DO UPDATE '
                             'SET date_from=EXCLUDED.date_from,date_to=EXCLUDED.date_to,confirmed=EXCLUDED.confirmed,'
                             'updated_by=EXCLUDED.updated_by,updated_at=CURRENT_TIMESTAMP',
                             (year,row['period'],row['date_from'],row['date_to'],row['confirmed'],teacher_id))
    if has_request_context():
        g.pop('school_calendars', None)
    return get_calendar(year)


def period_range(period, year=None):
    year = validate_year(year or school_today().year)
    try:
        number = int(str(period))
    except (TypeError, ValueError):
        raise ValueError('Selecciona un bimestre entre 1 y 4.') from None
    if number not in (1, 2, 3, 4):
        raise ValueError('Selecciona un bimestre entre 1 y 4.')
    row = get_calendar(year)['periods'][number - 1]
    return str(row['date_from']), str(row['date_to']), f'Bimestre {number}'


def current_term():
    today = school_today()
    rows = get_calendar(today.year)['periods']
    for row in rows:
        if today <= row['date_to']:
            return today.year, row['period']
    return today.year, 4
