"""Preserve institutional AD/A/B/C records without inventing numeric grades or dates."""
from collections import Counter
from pathlib import Path
import hashlib
import re
import unicodedata

from config import Config
from services import db_service

DIMENSIONS = (
    ('comprehension', 'Comprensión de los contenidos'),
    ('application', 'Aplicación de los conocimientos adquiridos'),
    ('completion', 'Cumplimiento de las actividades académicas'),
    ('homework', 'Realización de tareas'),
    ('resolution', 'Resolución de actividades académicas'),
)
RATINGS = {'AD', 'A', 'B', 'C'}
_records = []


def name_key(value):
    # Word order differs between the roster and the school's surname-first register.
    value = str(value).casefold().replace('ñ', '\ue000')
    value = ''.join(char for char in unicodedata.normalize('NFD', value) if not unicodedata.combining(char))
    words = re.findall(r'[^\W\d_]+', value.replace('\ue000', 'ñ'), flags=re.UNICODE)
    return tuple(sorted(words))


def modal_rating(values):
    if len(values) != len(DIMENSIONS) or any(value not in RATINGS for value in values):
        raise ValueError('Cada alumno debe tener cinco indicadores con valores AD, A, B o C.')
    frequencies = Counter(values)
    maximum = max(frequencies.values())
    # The supplied INDEX/MATCH/COUNTIF formula selects the first tied modal value.
    return next(value for value in values if frequencies[value] == maximum)


def parse_workbook(source):
    from openpyxl import load_workbook
    path = Path(source)
    if not path.is_file() or path.suffix.casefold() != '.xlsx':
        raise ValueError('Indica un archivo XLSX institucional existente.')
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('El archivo supera el límite de 20 MB.')
    formulas = load_workbook(path, read_only=True, data_only=False)
    cached = load_workbook(path, read_only=True, data_only=True)
    if len(formulas.sheetnames) != 1:
        raise ValueError('Este importador requiere una hoja con el formato del registro institucional revisado.')
    sheet, data = formulas.active, cached.active
    try:
        grade = int(re.match(r'\s*([456])', str(data['B6'].value)).group(1))
        year = int(data['B7'].value)
        period = int(re.match(r'\s*([1-4])', str(data['F6'].value)).group(1))
    except (TypeError, ValueError, AttributeError):
        raise ValueError('No se pudo identificar grado, año y bimestre en las celdas B6, B7 y F6.') from None
    if not 2000 <= year <= 2100 or str(data['F7'].value).strip().casefold() != 'literal':
        raise ValueError('Se requiere un año válido y una escala expresamente literal.')
    for column, (_, expected) in zip('CDEFG', DIMENSIONS):
        if name_key(data[f'{column}11'].value) != name_key(expected):
            raise ValueError(f'El indicador de la columna {column} no coincide con el formato revisado.')
    records = []
    seen = set()
    for row in range(12, data.max_row + 1):
        number, name = data[f'A{row}'].value, data[f'B{row}'].value
        if not isinstance(number, (int, float)) or not name:
            continue
        key = name_key(name)
        if not key or key in seen:
            raise ValueError(f'Hay un nombre vacío o duplicado en la fila {row}.')
        seen.add(key)
        values = [str(data[f'{column}{row}'].value or '').strip().upper() for column in 'CDEFG']
        final = str(data[f'H{row}'].value or '').strip().upper()
        expected_final = modal_rating(values)
        formula = sheet[f'H{row}'].value
        formula = getattr(formula, 'text', formula)
        expected_formula = f'=INDEX(C{row}:G{row},MATCH(MAX(COUNTIF(C{row}:G{row},C{row}:G{row})),COUNTIF(C{row}:G{row},C{row}:G{row}),0))'
        if not isinstance(formula, str) or re.sub(r'\s+', '', formula).upper() != expected_formula:
            raise ValueError(f'La fórmula final de la fila {row} no coincide con la regla verificada; requiere revisión.')
        if final != expected_final:
            raise ValueError(f'El resultado guardado de la fila {row} no coincide con sus indicadores. Recalcula el archivo en Excel.')
        records.append({'name': str(name).strip(), 'source_row': row, 'ratings': dict(zip(dict(DIMENSIONS), values)),
                        'final_rating': final, 'academic_year': year, 'period': period, 'grade': grade})
    formulas.close()
    cached.close()
    if not records:
        raise ValueError('No hay alumnos con indicadores completos para importar.')
    return {'records': records, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_name': path.name}


def prepare_import(parsed, students):
    matches = {}
    for student in students:
        key = (int(student['grade']), name_key(f"{student.get('first_name') or ''} {student.get('last_name') or ''}"))
        matches.setdefault(key, []).append(int(student['id']))
    prepared = []
    for row in parsed['records']:
        candidates = matches.get((row['grade'], name_key(row['name'])), [])
        if len(candidates) != 1:
            raise ValueError(f'La fila {row["source_row"]} no coincide de forma única con un alumno del padrón y su grado.')
        prepared.append({key: value for key, value in row.items() if key not in ('name', 'grade')}
                        | {'student_id': candidates[0], 'source_sha256': parsed['source_sha256'], 'source_name': parsed['source_name']})
    return prepared


def import_records(records):
    for row in records:
        if (set(row.get('ratings', {})) != set(dict(DIMENSIONS))
                or modal_rating([row['ratings'][key] for key, _ in DIMENSIONS]) != row.get('final_rating')
                or not 2000 <= int(row.get('academic_year', 0)) <= 2100 or int(row.get('period', 0)) not in (1,2,3,4)
                or int(row.get('student_id', 0)) <= 0 or int(row.get('source_row', 0)) <= 0
                or not re.fullmatch(r'[a-f0-9]{64}', str(row.get('source_sha256') or ''))):
            raise ValueError('El registro literal no cumple la validación institucional.')
    if Config.USE_MOCK_DATA:
        raise ValueError('La importación institucional requiere PostgreSQL real; no se escriben datos reales en el almacén ficticio.')
    from psycopg.types.json import Jsonb
    inserted = 0
    with db_service.get_connection() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s,%s)', (20261115, 8001))
        for row in records:
            existing = conn.execute('SELECT ratings,final_rating,source_sha256 FROM student_literal_history '
                                    'WHERE student_id=%s AND academic_year=%s AND period=%s AND subject=%s FOR UPDATE',
                                    (row['student_id'],row['academic_year'],row['period'],'computacion')).fetchone()
            if existing:
                if existing['ratings'] != row['ratings'] or existing['final_rating'] != row['final_rating']:
                    raise ValueError('Existen registros diferentes para el mismo alumno y periodo; no se sobrescriben automáticamente.')
                continue
            conn.execute('INSERT INTO student_literal_history '
                         '(student_id,academic_year,period,ratings,final_rating,source_sha256,source_name,source_row) '
                         'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                         (row['student_id'],row['academic_year'],row['period'],Jsonb(row['ratings']),row['final_rating'],
                          row['source_sha256'],row['source_name'],row['source_row']))
            inserted += 1
    return inserted


def fetch_history(student_id=None, grade=None, year=None, period=None):
    if Config.USE_MOCK_DATA:
        return [dict(row) for row in _records if (student_id is None or row['student_id'] == int(student_id))
                and (grade is None or row.get('grade') == int(grade)) and (year is None or row['academic_year'] == int(year))
                and (period is None or row['period'] == int(period))]
    clauses, params = [], []
    for column, value in [('h.student_id',student_id),('s.grade',grade),('h.academic_year',year),('h.period',period)]:
        if value is not None:
            clauses.append(column + '=%s'); params.append(int(value))
    with db_service.get_connection() as conn:
        return conn.execute("SELECT h.*,s.grade,CONCAT(s.first_name,' ',s.last_name) AS student_name FROM student_literal_history h "
                            'JOIN students s ON s.id=h.student_id' + (' WHERE '+ ' AND '.join(clauses) if clauses else '')
                            + ' ORDER BY s.grade,s.first_name,h.academic_year,h.period', tuple(params)).fetchall()


def readiness(records=None):
    records = fetch_history() if records is None else records
    groups = {}
    for row in records:
        groups.setdefault((row['student_id'], row.get('subject','computacion')), []).append((int(row['academic_year']), int(row['period'])))
    longitudinal = sum(len(set(periods)) > 1 for periods in groups.values())
    return {'records': len(records), 'students': len({row['student_id'] for row in records}),
            'periods': sorted({f"{row['academic_year']}-B{row['period']}" for row in records}),
            'students_with_later_period': longitudinal,
            'status': 'INSUFFICIENT_LONGITUDINAL_HISTORY' if longitudinal == 0 else 'REQUIRES_TRAINING_VALIDATION',
            'model_trained': False,
            'message': ('Se conserva el historial literal. Hace falta un resultado de otro periodo para evaluar predicción temporal.'
                        if longitudinal == 0 else 'Hay periodos posteriores; se requiere preparar y validar un entrenamiento separado.'),
            'same_period_final_is_derived': True}
