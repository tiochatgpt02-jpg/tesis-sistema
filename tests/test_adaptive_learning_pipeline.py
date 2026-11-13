import json

import pytest

from app import app
from config import Config
from services import db_service
from services.adaptive_learning_service import build_adaptive_learning_profile
from services.ai_game_generator_service import AIGameGeneratorService


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    monkeypatch.setattr(db_service, '_use_mock', lambda: True)


@pytest.fixture
def client():
    app.config.update(TESTING=True, SECRET_KEY='adaptive-test-secret')
    with app.test_client() as test_client:
        yield test_client


def _teacher(client):
    with client.session_transaction() as session:
        session.update(is_authenticated=True, user='profesor1', user_id=1, user_role='teacher')


def _student(client):
    with client.session_transaction() as session:
        session.update(is_authenticated=True, user='alumno1', student_id=1, user_role='student', user_grade=5)


def test_low_performance_profile_uses_evidence_and_recommends_easy_difficulty():
    profile = build_adaptive_learning_profile(1)

    assert profile['weak_topics']
    assert profile['weak_topics'][0]['evidence_count'] >= 1
    assert profile['recommended_difficulty'] == 'easy'
    assert profile['evidence_summary']['notes'] >= 1
    assert profile['risk_level']


def test_adaptive_generation_sends_weak_topic_and_difficulty_to_ollama(client, monkeypatch):
    _teacher(client)
    captured = {}
    response = {
        'game_type': 'multiple_choice',
        'title': 'Reto de fracciones',
        'instruction': 'Elige la respuesta correcta.',
        'content': {
            'question': '¿Qué indica el numerador?',
            'options': ['Las partes que tomamos', 'El color del dibujo', 'El nombre del juego'],
            'answer': 'Las partes que tomamos',
            'explanation': 'El material explica que el numerador indica las partes tomadas.'
        }
    }

    def fake_ollama(cls, prompt, timeout=120):
        captured['prompt'] = prompt
        return json.dumps(response)

    monkeypatch.setattr(AIGameGeneratorService, '_call_ollama', classmethod(fake_ollama))
    created = client.post('/teacher/api/students/1/adaptive-games', json={'material_id': 1, 'game_type': 'multiple_choice'})

    assert created.status_code == 201
    assert created.get_json()['status'] == 'PENDING_REVIEW'
    assert 'Tema a reforzar:' in captured['prompt']
    assert 'Dificultad requerida: easy' in captured['prompt']
    db_service.delete_ai_generated_game(created.get_json()['game_id'])


def test_adaptive_game_requires_teacher_review_and_only_published_game_reaches_student(client):
    _teacher(client)
    created = client.post('/teacher/api/students/1/adaptive-games', json={'material_id': 1})
    assert created.status_code == 201
    game_id = created.get_json()['game_id']
    assert created.get_json()['status'] == 'PENDING_REVIEW'

    _student(client)
    hidden = client.get('/student/api/topics/4/ai-games').get_json()['games']
    assert not any(game['id'] == game_id for game in hidden)
    assert client.post(f'/student/api/ai-games/{game_id}/play', json={'answer': 'x'}).status_code == 403

    _teacher(client)
    assert client.post(f'/teacher/api/ai-games/{game_id}/approve').status_code == 200
    assert client.post(f'/teacher/api/ai-games/{game_id}/publish').status_code == 200

    _student(client)
    published = client.get('/student/api/topics/4/ai-games').get_json()['games']
    assert any(game['id'] == game_id for game in published)
    training = client.get('/student/api/adaptive-learning').get_json()['training']
    assert training['recommended_activity']['type'] == 'published_ai_game'
    assert training['recommended_activity']['game_id'] == game_id
    db_service.delete_ai_generated_game(game_id)


def test_teacher_can_read_adaptive_analysis_but_student_cannot_generate(client):
    _teacher(client)
    analysis = client.get('/teacher/api/students/1/adaptive-analysis')
    assert analysis.status_code == 200
    assert 'weak_topics' in analysis.get_json()['analysis']

    _student(client)
    denied = client.post('/teacher/api/students/1/adaptive-games', json={'material_id': 1})
    assert denied.status_code == 403
