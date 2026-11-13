"""Add fictitious demo users without resetting an existing school database."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from werkzeug.security import generate_password_hash
from services.db_service import get_connection


def main():
    password = os.getenv('DEMO_PASSWORD')
    if not password or len(password) < 12:
        raise SystemExit('Configura DEMO_PASSWORD con al menos 12 caracteres antes de crear cuentas.')
    with get_connection() as conn:
        conn.execute('INSERT INTO users (username,password_hash,role,first_name,last_name) VALUES (%s,%s,%s,%s,%s) '
                     'ON CONFLICT(username) DO NOTHING',
                     ('docente_demo', generate_password_hash(password), 'teacher', 'Docente', 'Demostracion'))
        for grade in (4,5,6):
            code = f'DEMO-{grade}'
            row = conn.execute('SELECT id FROM students WHERE student_code=%s',(code,)).fetchone()
            sid = row['id'] if row else conn.execute(
                "INSERT INTO students (student_code,first_name,last_name,grade,section) VALUES (%s,%s,%s,%s,'A') RETURNING id",
                (code,f'Alumno {grade}','Demostracion',grade)).fetchone()['id']
            conn.execute('INSERT INTO users (username,password_hash,role,first_name,last_name,grade,student_id) '
                         'VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(username) DO NOTHING',
                         (f'alumno_demo_{grade}',generate_password_hash(password),'student',f'Alumno {grade}','Demostracion',grade,sid))
            conn.execute('INSERT INTO student_progress (student_id,study_time) VALUES (%s,%s) ON CONFLICT(student_id) DO NOTHING',(sid,'0h'))
    print('Cuentas ficticias creadas: docente_demo, alumno_demo_4, alumno_demo_5, alumno_demo_6.')
    print('Las cuentas existentes no fueron modificadas.')


if __name__ == '__main__':
    main()
