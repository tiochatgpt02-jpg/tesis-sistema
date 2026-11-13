import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from config import Config


def test_seeded_teacher_password_is_hashed_and_login_succeeds(monkeypatch):
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    client = app.test_client()
    response = client.post('/login', data={'username': 'profesor1', 'password': 'Admin123'})
    assert response.status_code == 302
    assert '/teacher/' in response.headers['Location']


def test_invalid_password_fails_login(monkeypatch):
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    client = app.test_client()
    response = client.post('/login', data={'username': 'profesor1', 'password': 'incorrecta'})
    assert response.status_code == 200
    assert 'Credenciales inválidas' in response.get_data(as_text=True)


def test_student_login_requires_matching_section(monkeypatch):
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    client = app.test_client()

    response = client.post('/login', data={'username': 'alumno1', 'password': 'Alumno123', 'grade': '5', 'section': 'B'})
    assert response.status_code == 200
    assert 'La sección seleccionada no coincide' in response.get_data(as_text=True)

    response = client.post('/login', data={'username': 'alumno1', 'password': 'Alumno123', 'grade': '5', 'section': 'A'})
    assert response.status_code == 302
    assert '/student/' in response.headers['Location']

