import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

from flask import Flask, request, session, jsonify, redirect, url_for
from controllers.auth_controller import auth_blueprint
from controllers.teacher_controller import teacher_blueprint
from controllers.teacher_assessment_controller import teacher_assessment_blueprint
from controllers.teacher_notes_controller import teacher_notes_blueprint
from controllers.teacher_reports_controller import teacher_reports_blueprint
from controllers.teacher_export_controller import teacher_export_blueprint
from controllers.teacher_ai_games_controller import teacher_ai_games_blueprint
from controllers.student_controller import student_blueprint
from controllers.ai_controller import ai_blueprint
from controllers.settings_controller import settings_blueprint
from config import Config
from services.db_service import test_connection
from services.ai_service import check_ollama_status

app = Flask(__name__, template_folder='views', static_folder='static')
app.secret_key = Config.SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
                  MAX_CONTENT_LENGTH=21 * 1024 * 1024)
if os.getenv('APP_ENV') == 'production':
    if Config.USE_MOCK_DATA or Config.SECRET_KEY == 'dev-secret-change-in-production':
        raise RuntimeError('Producción requiere SECRET_KEY propia y USE_MOCK_DATA=false.')


@app.before_request
def protect_teacher_routes():
    if request.path.startswith('/teacher'):
        if not session.get('is_authenticated') or session.get('user_role') != 'teacher':
            if '/api/' in request.path:
                return jsonify({'success': False, 'error': 'Requiere sesión docente.'}), (403 if session.get('is_authenticated') else 401)
            return redirect(url_for('auth.login'))
    if request.path.startswith('/static/uploads/student_work/'):
        if not session.get('is_authenticated'):
            return jsonify({'error': 'No autorizado'}), 401
        from services.db_service import fetch_submissions
        from services.file_storage_service import read_bytes
        from flask import send_file, abort
        from io import BytesIO
        submissions = fetch_submissions(student_id=session.get('student_id')) if session.get('user_role') == 'student' else fetch_submissions()
        permitted = next((s for s in submissions if s.get('file_path') == request.path or s.get('file_url') == request.path), None)
        if not permitted or session.get('user_role') not in {'student', 'teacher'}:
            abort(404)
        content = read_bytes(request.path)
        if content is not None:
            return send_file(BytesIO(content), as_attachment=True, download_name=permitted.get('file_name') or 'trabajo')
    if request.path.startswith('/static/uploads/presentations/'):
        # Students use the scoped /student/api/presentations/<id>/file route.
        if not session.get('is_authenticated') or session.get('user_role') != 'teacher':
            return jsonify({'error': 'Usa la descarga autorizada de tu material.'}), 403


@app.after_request
def protect_private_responses(response):
    if request.path.startswith(('/teacher', '/student', '/files', '/static/uploads/')):
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


def plain_summary(value, max_len=200):
    if not value:
        return ''
    text = str(value)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'[#*`_~\-]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + '...'


app.jinja_env.filters['plain_summary'] = plain_summary

app.register_blueprint(auth_blueprint)
app.register_blueprint(teacher_blueprint)
app.register_blueprint(teacher_assessment_blueprint)
app.register_blueprint(teacher_notes_blueprint)
app.register_blueprint(teacher_reports_blueprint)
app.register_blueprint(teacher_export_blueprint)
app.register_blueprint(teacher_ai_games_blueprint)
app.register_blueprint(student_blueprint)
app.register_blueprint(ai_blueprint)
app.register_blueprint(settings_blueprint)


@app.route('/health')
def health():
    ok, msg = test_connection()
    ollama = check_ollama_status()
    return {
        'status': 'ok' if ok else 'error',
        'database': 'connected' if ok else 'unavailable',
        'mock_mode': Config.USE_MOCK_DATA,
        'ollama': ollama,
    }, 200 if ok else 503


@app.route('/live')
def live():
    return {'status': 'ok'}


if __name__ == '__main__':
    ok, msg = test_connection()
    if ok:
        print(f'[DB] {msg}')
    else:
        print(f'[DB] ERROR: {msg}')
        print('[DB] Ejecuta: python scripts/setup_db.py')
        print('[DB] O copia .env.example a .env y configura tus credenciales PostgreSQL')
    ollama = check_ollama_status()
    if ollama.get('running') and ollama.get('model_available'):
        print(f"[Ollama] Listo · modelo: {ollama.get('model')}")
    elif ollama.get('running'):
        print(f"[Ollama] Encendido, pero falta el modelo {ollama.get('model')}. Ejecuta: ollama pull {ollama.get('model')}")
    else:
        print('[Ollama] No responde. Abre Ollama o ejecuta: ollama serve')
    debug_mode = os.getenv('FLASK_DEBUG', '0').strip().lower() in {'1', 'true', 'yes'}
    app.run(debug=debug_mode)
