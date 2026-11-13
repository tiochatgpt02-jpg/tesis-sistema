"""Prueba de humo local para el recorrido PPT -> Ollama -> alumno -> PostgreSQL.

No usa contraseñas ni las imprime. Requiere el PPT de demostración ya registrado
en topic_presentations.id=1 y las cuentas alumno4_demo, alumno5_demo y alumno6_demo.
"""
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app
from config import Config


def connection():
    return psycopg.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        dbname=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
    )


def set_session(client, username, role, grade=None, student_id=None, user_id=None):
    with client.session_transaction() as session:
        session['is_authenticated'] = True
        session['user'] = username
        session['user_role'] = role
        if grade is not None:
            session['user_grade'] = grade
        if student_id is not None:
            session['student_id'] = student_id
        if user_id is not None:
            session['user_id'] = user_id


def main():
    with connection() as db:
        teacher_id = db.execute(
            'SELECT id FROM users WHERE username = %s', ('profesor1',),
        ).fetchone()[0]
        students = {
            row[1]: {'username': row[0], 'student_id': row[2]}
            for row in db.execute(
                'SELECT username, grade, student_id FROM users '
                'WHERE username IN (%s, %s, %s)',
                ('alumno4_demo', 'alumno5_demo', 'alumno6_demo'),
            ).fetchall()
        }

    missing = {grade for grade in (4, 5, 6) if grade not in students}
    if missing:
        raise RuntimeError(f'Faltan cuentas demo para los grados: {sorted(missing)}')

    app.config['TESTING'] = True
    cycle_topic_id = 10

    # Los alumnos de 4.º y 6.º no pueden abrir contenido de 5.º.
    access = {}
    for grade, expected_status in ((4, 404), (5, 200), (6, 404)):
        client = app.test_client()
        student = students[grade]
        set_session(client, student['username'], 'student', grade, student['student_id'])
        response = client.get(f'/student/api/topics/{cycle_topic_id}/ai-games')
        access[grade] = response.status_code
        if response.status_code != expected_status:
            raise RuntimeError(f'Control de grado falló para {grade}.º: HTTP {response.status_code}')

    teacher = app.test_client()
    set_session(teacher, 'profesor1', 'teacher', user_id=teacher_id)
    generated = teacher.post(
        '/teacher/api/presentations/1/generate-game',
        json={'game_type': 'multiple_choice'},
    )
    payload = generated.get_json() or {}
    if generated.status_code != 201 or payload.get('source') != 'ollama':
        raise RuntimeError(f'La generación no usó Ollama correctamente: {payload}')
    game_id = payload['game_id']
    content = (payload.get('game') or {}).get('content_json') or {}
    answer = content.get('answer')
    if not answer or answer not in content.get('options', []):
        raise RuntimeError('El juego generado no tiene una respuesta válida entre sus opciones.')

    if teacher.post(f'/teacher/api/ai-games/{game_id}/approve').status_code != 200:
        raise RuntimeError('No se pudo aprobar el juego generado.')
    if teacher.post(f'/teacher/api/ai-games/{game_id}/publish').status_code != 200:
        raise RuntimeError('No se pudo publicar el juego aprobado.')

    student = students[5]
    learner = app.test_client()
    set_session(learner, student['username'], 'student', 5, student['student_id'])
    listed = learner.get(f'/student/api/topics/{cycle_topic_id}/ai-games').get_json() or {}
    if not any(game.get('id') == game_id for game in listed.get('games', [])):
        raise RuntimeError('El juego publicado no aparece para el alumno de 5.º.')
    played = learner.post(
        f'/student/api/ai-games/{game_id}/play',
        json={'answer': answer, 'time_spent': 8},
    )
    played_data = played.get_json() or {}
    if played.status_code != 200 or not played_data.get('is_correct'):
        raise RuntimeError(f'El alumno no pudo completar el juego: {played_data}')

    with connection() as db:
        attempts = db.execute(
            'SELECT COUNT(*) FROM student_game_attempts WHERE student_id = %s AND game_id = %s',
            (student['student_id'], game_id),
        ).fetchone()[0]
    if attempts < 1:
        raise RuntimeError('No se guardó el intento del juego en PostgreSQL.')

    print({
        'grade_access_http': access,
        'ollama_model': Config.OLLAMA_MODEL,
        'source': payload['source'],
        'game_id': game_id,
        'attempts_saved': attempts,
    })


if __name__ == '__main__':
    main()
