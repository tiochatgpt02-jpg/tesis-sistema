"""
Tests automatizados para GOAL 5: Juegos Interactivos de Reforzamiento.
Verifica:
1. Existencia y estructura de los 3 juegos (Opción múltiple, Verdadero/Falso, Completar).
2. Lógica de juego interactivo y retroalimentación pedagógica inmediata.
3. Persistencia de intentos en la tabla student_game_attempts y sincronización en student_notes.
4. Flujo inteligente de detección de debilidades y recomendación de juegos específicos.
5. Asociación estricta de cada juego con su respectivo tema curricular.
"""
import pytest
from datetime import datetime, timezone
from app import app
from services.db_service import (
    fetch_student_game_attempts,
    fetch_reinforcement_games_catalog,
    fetch_reinforcement_game_by_id,
)
from services.reinforcement_games_service import (
    detect_weaknesses_and_recommend_games,
    evaluate_game_submission,
)


@pytest.fixture(autouse=True)
def enable_mock_mode(monkeypatch):
    from config import Config
    from services import db_service
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    monkeypatch.setattr(db_service, '_use_mock', lambda: True)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_student_client(client):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True
    return client


def test_fetch_reinforcement_games_catalog_delivers_three_canonical_games(authenticated_student_client):
    """
    Comprueba que el catálogo contiene exactamente los 3 juegos requeridos con sus tipos y temas:
    - Juego 1: Opción múltiple (¿Cuánto es 5x5? 20, 25, 30)
    - Juego 2: Verdadero/Falso (La tierra gira alrededor del sol)
    - Juego 3: Completar (La fotosíntesis ocurre en ______)
    """
    resp = authenticated_student_client.get('/student/api/reinforcement-games')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    games = data['games']
    assert len(games) == 3

    # Juego 1
    g1 = next(g for g in games if g['id'] == 1)
    assert g1['game_type'] == 'opcion_multiple'
    assert '¿cuánto es 5x5?' in g1['question'].lower()
    assert '20' in g1['options']
    assert '25' in g1['options']
    assert '30' in g1['options']
    assert g1['topic_id'] is not None
    assert 'multiplicación' in g1['topic_title'].lower()

    # Juego 2
    g2 = next(g for g in games if g['id'] == 2)
    assert g2['game_type'] == 'verdadero_falso'
    assert 'la tierra gira alrededor del sol' in g2['question'].lower()
    assert 'Verdadero' in g2['options']
    assert 'Falso' in g2['options']
    assert g2['topic_id'] is not None

    # Juego 3
    g3 = next(g for g in games if g['id'] == 3)
    assert g3['game_type'] == 'completar'
    assert 'fotosíntesis ocurre en' in g3['question'].lower()
    assert g3['topic_id'] is not None


def test_play_game_1_multiple_choice_persists_attempt_and_evaluates_correctness(authenticated_student_client):
    """
    Juego 1: Alumno responde ¿Cuánto es 5x5?
    - Si responde '25': acierto (score 20, percentage 100%, feedback positivo).
    - Si responde '20': error (score 8, percentage 40%, feedback explicativo).
    Verifica guardado en student_game_attempts.
    """
    # 1. Intento correcto
    resp_ok = authenticated_student_client.post('/student/api/reinforcement-games/1/play', json={
        'answer': '25',
        'time_spent': 12,
    })
    assert resp_ok.status_code == 200
    data_ok = resp_ok.get_json()
    assert data_ok['success'] is True
    res_ok = data_ok['result']
    assert res_ok['is_correct'] is True
    assert res_ok['score'] == 20.0
    assert res_ok['percentage'] == 100.0
    assert '25' in res_ok['feedback']
    attempt_id = data_ok['attempt_id']
    assert attempt_id is not None

    # 2. Intento incorrecto
    resp_fail = authenticated_student_client.post('/student/api/reinforcement-games/1/play', json={
        'answer': '20',
        'time_spent': 8,
    })
    assert resp_fail.status_code == 200
    data_fail = resp_fail.get_json()
    assert data_fail['success'] is True
    res_fail = data_fail['result']
    assert res_fail['is_correct'] is False
    assert res_fail['score'] < 20.0

    # 3. Comprobar que los intentos quedaron guardados en student_game_attempts
    attempts = fetch_student_game_attempts(student_id=1, game_id=1)
    assert len(attempts) >= 2
    assert any(a['is_correct'] is True for a in attempts)
    assert any(a['is_correct'] is False for a in attempts)


def test_play_game_2_true_false_evaluation(authenticated_student_client):
    """
    Juego 2: Alumno responde 'La tierra gira alrededor del sol'
    - 'Verdadero' -> Correcto
    - 'Falso' -> Incorrecto
    """
    resp_true = authenticated_student_client.post('/student/api/reinforcement-games/2/play', json={
        'answer': 'Verdadero',
        'time_spent': 10,
    })
    assert resp_true.status_code == 200
    assert resp_true.get_json()['result']['is_correct'] is True

    resp_false = authenticated_student_client.post('/student/api/reinforcement-games/2/play', json={
        'answer': 'Falso',
        'time_spent': 7,
    })
    assert resp_false.status_code == 200
    assert resp_false.get_json()['result']['is_correct'] is False


def test_play_game_3_fill_in_the_blank_photosynthesis(authenticated_student_client):
    """
    Juego 3: Alumno responde 'La fotosíntesis ocurre en ______'
    - 'las hojas' (o 'hojas') -> Correcto
    - 'las piedras' -> Incorrecto
    """
    resp_ok = authenticated_student_client.post('/student/api/reinforcement-games/3/play', json={
        'answer': 'las hojas',
        'time_spent': 15,
    })
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()['result']['is_correct'] is True

    resp_fail = authenticated_student_client.post('/student/api/reinforcement-games/3/play', json={
        'answer': 'las piedras',
        'time_spent': 10,
    })
    assert resp_fail.status_code == 200
    assert resp_fail.get_json()['result']['is_correct'] is False


def test_weakness_detection_recommends_specific_games_flow():
    """
    Flujo:
    Alumno falla pregunta -> Sistema detecta debilidad -> Recomienda juego
    """
    # Caso 1: Debilidad detectada en Multiplicación
    recs_mult = detect_weaknesses_and_recommend_games(1, explicit_weak_topics=['Multiplicación', 'Tablas de multiplicar'])
    assert len(recs_mult) > 0
    top_mult = recs_mult[0]
    assert top_mult['id'] == 1
    assert 'multiplicación' in top_mult['topic_title'].lower()
    assert top_mult['priority'] == 'ALTA'

    # Caso 2: Debilidad detectada en Fotosíntesis
    recs_foto = detect_weaknesses_and_recommend_games(1, explicit_weak_topics=['Fotosíntesis', 'Plantas'])
    assert len(recs_foto) > 0
    top_foto = recs_foto[0]
    assert top_foto['id'] == 3
    assert 'fotosíntesis' in top_foto['topic_title'].lower()
    assert top_foto['priority'] == 'ALTA'

    # Caso 3: Debilidad detectada en Sistema Solar
    recs_astro = detect_weaknesses_and_recommend_games(1, explicit_weak_topics=['Sistema Solar', 'Tierra y Sol'])
    assert len(recs_astro) > 0
    top_astro = recs_astro[0]
    assert top_astro['id'] == 2
    assert top_astro['priority'] == 'ALTA'


def test_unmatched_weak_topics_do_not_recommend_unrelated_games():
    recommendations = detect_weaknesses_and_recommend_games(
        1,
        explicit_weak_topics=['Tema exclusivo de la presentación'],
    )

    assert recommendations == []


def test_student_can_fetch_game_history(authenticated_student_client):
    """
    Verifica que el alumno puede consultar su historial de juegos interactivos practicados.
    """
    # Registrar al menos una práctica
    authenticated_student_client.post('/student/api/reinforcement-games/1/play', json={
        'answer': '25',
        'time_spent': 14,
    })

    resp = authenticated_student_client.get('/student/api/reinforcement-games/attempts')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert isinstance(data['attempts'], list)
    assert len(data['attempts']) >= 1


def test_evaluation_failure_triggers_game_recommendation_in_result(authenticated_student_client):
    """
    GOAL 5 Flujo Completo:
    Alumno rinde examen, falla pregunta de Multiplicación -> Sistema detecta debilidad
    y retorna recommended_games conteniendo el Juego 1 (Multiplicación).
    """
    get_resp = authenticated_student_client.get('/student/api/topics/4/evaluation')
    assert get_resp.status_code == 200
    questions = get_resp.get_json()['evaluation']['questions']

    # Responder fallando la pregunta de multiplicación
    answers = {}
    for idx, q in enumerate(questions):
        sub = str(q.get('subtopic', '')).lower()
        q_text = str(q.get('question', '')).lower()
        if 'multiplic' in sub or 'multiplic' in q_text:
            answers[str(idx)] = "Respuesta equivocada en multiplicación"
        else:
            answers[str(idx)] = q.get('answer', '')

    started_at = datetime.now(timezone.utc).isoformat()
    submit_resp = authenticated_student_client.post('/student/api/topics/4/evaluation', json={
        'answers': answers,
        'attempt_id': get_resp.get_json()['evaluation']['attempt_id'],
        'started_at': started_at,
        'time_spent': 180,
    })

    assert submit_resp.status_code == 200
    submit_data = submit_resp.get_json()
    assert submit_data['success'] is True
    result = submit_data['result']

    # Comprobar que en temas a reforzar está Multiplicación
    reinforce = result['reinforce_topics']
    assert any('multiplic' in str(t).lower() for t in reinforce)

    # Comprobar que el sistema recomendó el juego de reforzamiento correspondiente (Juego 1)
    rec_games = result.get('recommended_games') or []
    assert len(rec_games) >= 1
    assert any(g['id'] == 1 for g in rec_games)


def test_student_dashboard_html_contains_reinforcement_games_section(authenticated_student_client):
    """
    Comprueba que el dashboard del estudiante incluye el contenedor de juegos de reforzamiento.
    """
    resp = authenticated_student_client.get('/student/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'reinforcement-recommendations-panel' in html
    assert 'reinforcement-recommendations-list' in html
    assert 'Juegos recomendados para reforzar tus temas' in html
