from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.db_service import ensure_student_record_for_user, fetch_student_by_id, fetch_user_by_username
from services.email_service import send_security_code_via_email, send_security_code_via_sms
from services.two_step_service import generate_code, code_expiration_time, is_code_valid
from config import Config
from datetime import datetime
from werkzeug.security import check_password_hash

auth_blueprint = Blueprint('auth', __name__)


def _password_is_valid(user, password):
    if not user:
        return False

    password_hash = str(user.get('password_hash', '') or '')
    submitted_password = str(password or '')

    try:
        if check_password_hash(password_hash, submitted_password):
            return True
    except (TypeError, ValueError):
        pass

    # Plaintext passwords are accepted only by the isolated demonstration store.
    if Config.USE_MOCK_DATA and not password_hash.startswith(('scrypt:', 'pbkdf2:')):
        import hmac
        return hmac.compare_digest(password_hash, submitted_password)
    return False


@auth_blueprint.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password')
        selected_grade = request.form.get('grade')

        user = fetch_user_by_username(username)

        if user and user.get('role') == 'student':
            try:
                selected_grade_value = int(selected_grade) if selected_grade not in (None, '') else None
            except (TypeError, ValueError):
                selected_grade_value = None

            expected_grade = user.get('grade')
            if expected_grade is None or selected_grade_value is None:
                return render_template('login.html', error='Debes seleccionar el grado correcto para este alumno.')
            if int(expected_grade) != selected_grade_value:
                return render_template('login.html', error='El grado seleccionado no coincide con este alumno.')
            selected_section = str(request.form.get('section') or 'A').strip().upper()
            if selected_section != str(user.get('section') or 'A').upper():
                return render_template('login.html', error='La sección seleccionada no coincide con este alumno.')

        password_valid = _password_is_valid(user, password)
        if password_valid:
            session.clear()
            session['user'] = username
            # Las acciones docentes que se persisten (PPT, juegos y evaluaciones)
            # necesitan el usuario real, no un valor predeterminado inexistente.
            session['user_id'] = user.get('id')
            session['user_role'] = user.get('role')
            session['user_grade'] = user.get('grade')
            session['user_section'] = (user.get('section') or 'A')
            session['student_id'] = ensure_student_record_for_user(user, section=session['user_section']) if user.get('role') == 'student' else None
            session['student_name'] = f"{user.get('first_name', '')} {user.get('last_name', username)}".strip()
            session['teacher_name'] = f"{user.get('first_name', 'Prof.')} {user.get('last_name', '')}".strip()
            session['is_authenticated'] = True

            if session.get('user_role') == 'teacher':
                return redirect(url_for('teacher.teacher_home'))
            return redirect(url_for('student.student_home'))

        return render_template('login.html', error='Credenciales inválidas')
    return render_template('login.html')


@auth_blueprint.route('/two-step', methods=['GET', 'POST'])
def two_step():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if Config.USE_MOCK_DATA:
        session['is_authenticated'] = True
        if session.get('user_role') == 'teacher':
            return redirect(url_for('teacher.teacher_home'))
        return redirect(url_for('student.student_home'))

    if request.method == 'POST':
        code = request.form.get('code')
        stored_code = session.get('two_step_code')
        expires = session.get('two_step_expires')

        if not stored_code or not expires:
            session['is_authenticated'] = True
            role = session.get('user_role')
            if role == 'teacher':
                return redirect(url_for('teacher.teacher_home'))
            return redirect(url_for('student.student_home'))

        try:
            valid = is_code_valid(code, stored_code, datetime.fromisoformat(expires))
        except Exception:
            valid = False

        if valid:
            session['is_authenticated'] = True
            role = session.get('user_role')
            if role == 'teacher':
                return redirect(url_for('teacher.teacher_home'))
            return redirect(url_for('student.student_home'))

        return render_template('two_step.html', error='Código inválido o expirado')
    return render_template('two_step.html')


@auth_blueprint.route('/dashboard')
def dashboard():
    if 'user' not in session or not session.get('is_authenticated'):
        return redirect(url_for('auth.login'))
    role = session.get('user_role')
    if role == 'teacher':
        return redirect(url_for('teacher.teacher_home'))
    return redirect(url_for('student.student_home'))


@auth_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
