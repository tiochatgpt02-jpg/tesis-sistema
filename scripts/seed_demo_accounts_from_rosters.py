"""Crea una cuenta de demostración por grado desde los padrones Excel entregados.

No imprime contraseñas ni nombres completos. Es idempotente y solo crea los
usuarios alumno4_demo, alumno5_demo y alumno6_demo que falten.
"""
from pathlib import Path
import re
import sys

from openpyxl import load_workbook
import psycopg
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import Config

ROSTERS = {
    4: ROOT.parent.parent / '4to_primaria.xlsx',
    5: ROOT.parent.parent / '5to prim.xlsx',
    6: ROOT.parent.parent / '6to prim.xlsx',
}
NAME_PATTERN = re.compile(r'^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ .-]+,\s*[A-ZÁÉÍÓÚÑ]')


def first_student_name(path: Path) -> tuple[str, str]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for value in row:
                    candidate = str(value or '').strip()
                    if not NAME_PATTERN.match(candidate):
                        continue
                    last_name, first_name = (part.strip() for part in candidate.split(',', 1))
                    return first_name.title(), last_name.title()
    finally:
        workbook.close()
    raise ValueError(f'No se encontró un alumno válido en {path.name}.')


def main() -> None:
    created = []
    with psycopg.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        dbname=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
    ) as connection:
        for grade, path in ROSTERS.items():
            if not path.is_file():
                raise FileNotFoundError(f'No se encontró el padrón de {grade}.º: {path.name}')
            username = f'alumno{grade}_demo'
            if connection.execute('SELECT 1 FROM users WHERE username = %s', (username,)).fetchone():
                continue

            first_name, last_name = first_student_name(path)
            student_id = connection.execute(
                'INSERT INTO students (student_code, first_name, last_name, grade, section, progress) '
                'VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                (f'DEMO-G{grade}-01', first_name, last_name, grade, 'A', 0),
            ).fetchone()[0]
            connection.execute(
                'INSERT INTO users (username, password_hash, role, first_name, last_name, email, grade, student_id) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (
                    username, generate_password_hash('Alumno123'), 'student', first_name,
                    last_name, f'{username}@demo.local', grade, student_id,
                ),
            )
            created.append({'username': username, 'grade': grade})
    print({'created': created, 'count': len(created)})


if __name__ == '__main__':
    main()
