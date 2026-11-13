import pytest
from datetime import datetime, timezone
from app import app
from services.db_service import (
    fetch_student_assessment_attempts,
    fetch_assessment_attempt_by_id,
    fetch_published_assessment_for_topic,
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


def test_formal_assessment_delivers_fifteen_questions(client):
    """
    GOAL 4: Comprueba que la evaluación formal por tema contiene exactamente 15 preguntas.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    resp = client.get('/student/api/topics/4/evaluation')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['status'] == 'PUBLISHED'
    assert data['published'] is True

    evaluation = data['evaluation']
    assert evaluation['topic_id'] == 4
    questions = evaluation['questions']
    assert len(questions) == 15, f"Se esperaban exactamente 15 preguntas, se obtuvieron {len(questions)}"

    # Verificar estructura de cada pregunta
    for idx, q in enumerate(questions, 1):
        assert 'question' in q and len(q['question']) > 5
        assert 'options' in q and len(q['options']) >= 2
        assert 'answer' not in q
        assert q.get('approved') is True


def test_student_attempt_recorded_with_twelve_correct_and_eighty_percent(client):
    """
    GOAL 4: Simula un intento con 12 de 15 respuestas correctas (80%),
    verificando el guardado del intento en student_assessment_attempts
    y la identificación de 'Temas a reforzar' (- División, - Multiplicación).
    """
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    # 1. Obtener las 15 preguntas para conocer las respuestas esperadas
    get_resp = client.get('/student/api/topics/4/evaluation')
    evaluation = get_resp.get_json()['evaluation']
    questions = evaluation['questions']
    from services.learning_attempt_service import _attempts
    keys = _attempts[evaluation['attempt_id']]['questions']
    assert len(questions) == 15

    # 2. Responder 12 correctas y fallar a propósito 3 preguntas (ej: División y Multiplicación)
    # Identificamos índices con División y Multiplicación
    div_idx = None
    mult_idx = None
    for idx, q in enumerate(questions):
        sub = str(q.get('subtopic', '')).lower()
        q_text = str(q.get('question', '')).lower()
        if div_idx is None and ('divisi' in sub or 'divisi' in q_text):
            div_idx = idx
        elif mult_idx is None and ('multiplic' in sub or 'multiplic' in q_text):
            mult_idx = idx

    other_idx = None
    for idx in range(len(questions)):
        if idx != div_idx and idx != mult_idx:
            other_idx = idx
            break

    failed_indices = {div_idx, mult_idx, other_idx} - {None}
    assert len(failed_indices) == 3

    answers = {}
    for idx, q in enumerate(questions):
        if idx in failed_indices:
            answers[str(idx)] = "Respuesta equivocada deliberada"
        else:
            answers[str(idx)] = keys[idx]['answer']

    started_at = datetime.now(timezone.utc).isoformat()
    submit_resp = client.post('/student/api/topics/4/evaluation', json={
        'answers': answers,
        'attempt_id': evaluation['attempt_id'],
        'started_at': started_at,
        'time_spent': 240,
    })

    assert submit_resp.status_code == 200
    submit_data = submit_resp.get_json()
    assert submit_data['success'] is True
    assert 'attempt_id' in submit_data
    attempt_id = submit_data['attempt_id']

    result = submit_data['result']
    assert result['correct_answers'] == 12
    assert result['total_questions'] == 15
    assert result['percentage'] == 80.0
    assert result['score'] == 16.0
    assert result['time_spent'] > 0

    # Verificar que en 'Temas a reforzar' figuran División y Multiplicación
    reinforce = result['reinforce_topics']
    assert isinstance(reinforce, list)
    assert len(reinforce) > 0
    reinforce_str = " ".join(reinforce).lower()
    assert 'divisi' in reinforce_str
    assert 'multiplic' in reinforce_str

    # 3. Verificar persistencia directa en student_assessment_attempts
    saved_attempt = fetch_assessment_attempt_by_id(attempt_id)
    assert saved_attempt is not None
    assert saved_attempt['student_id'] == 1
    assert saved_attempt['score'] == 16.0
    assert saved_attempt['correct_answers'] == 12
    assert saved_attempt['total_questions'] == 15
    assert saved_attempt['percentage'] == 80.0
    assert 'date' in saved_attempt and saved_attempt['date']
    assert saved_attempt['time_spent'] > 0


def test_student_can_fetch_attempt_history(client):
    """
    GOAL 4: Verifica que el alumno puede consultar su historial de intentos de evaluación.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    from services.db_service import record_student_assessment_attempt
    record_student_assessment_attempt(1, 1, 12, 30)
    resp = client.get('/student/api/assessments/attempts')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert isinstance(data['attempts'], list)
    assert len(data['attempts']) >= 1


def test_perfect_score_fifteen_of_fifteen_has_empty_reinforce_topics(client):
    """
    GOAL 4: Si el alumno responde las 15 preguntas correctamente (15/15 = 100%),
    no debe haber temas a reforzar.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    get_resp = client.get('/student/api/topics/4/evaluation')
    evaluation = get_resp.get_json()['evaluation']
    questions = evaluation['questions']
    from services.learning_attempt_service import _attempts
    keys = _attempts[evaluation['attempt_id']]['questions']

    # Todas correctas
    answers = {str(idx): q['answer'] for idx, q in enumerate(keys)}

    submit_resp = client.post('/student/api/topics/4/evaluation', json={
        'answers': answers,
        'attempt_id': evaluation['attempt_id'],
        'started_at': datetime.now(timezone.utc).isoformat(),
        'time_spent': 180,
    })

    assert submit_resp.status_code == 200
    res = submit_resp.get_json()['result']
    assert res['correct_answers'] == 15
    assert res['total_questions'] == 15
    assert res['percentage'] == 100.0
    assert res['score'] == 20.0
    assert len(res['reinforce_topics']) == 0
