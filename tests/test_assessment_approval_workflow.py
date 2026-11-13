import pytest
from datetime import datetime, timezone
from app import app
from services.db_service import (
    create_assessment,
    update_assessment_status,
    fetch_assessment_by_id,
    fetch_assessment_by_id,
    create_question,
    update_question,
    delete_question,
    approve_question,
    fetch_published_assessment_for_topic,
    fetch_assessments_for_topic,
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


def test_ai_assessment_generation_creates_pending_review_with_unapproved_questions(client, monkeypatch):
    """
    Regla fundamental: La IA genera preguntas, pero NUNCA se publican automáticamente.
    Estado: GENERATED -> PENDING_REVIEW.
    Todas las preguntas generadas deben tener approved = False.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['teacher_id'] = 1
        sess['is_authenticated'] = True

    from controllers import teacher_assessment_controller

    monkeypatch.setattr(
        teacher_assessment_controller,
        'get_presentations_for_topic',
        lambda topic_id: [{'id': 1, 'topic_id': topic_id, 'session_number': 1}],
    )
    monkeypatch.setattr(
        teacher_assessment_controller.MaterialExtractorService,
        'extract_from_presentation_record',
        lambda presentation: {'raw_text': 'Contenido sobre redes e Internet.', 'title': 'Redes e Internet'},
    )
    monkeypatch.setattr(
        teacher_assessment_controller,
        'generate_questions_from_teacher_material',
        lambda *args, **kwargs: {
            'success': True,
            'source': 'fallback',
            'questions': [{
                'question': '¿Qué permite una red?',
                'options': ['Compartir información', 'Pintar', 'Cocinar'],
                'answer': 'Compartir información',
            }],
        },
    )

    response = client.post('/teacher/api/assessments/generate', json={
        'topic_id': 2,
        'title': 'Evaluación de Redes e Internet',
        'question_count': 3
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['status'] == 'PENDING_REVIEW'
    assert 'assessment_id' in data

    questions = data['questions']
    assert len(questions) >= 1
    # Ninguna pregunta debe estar aprobada automáticamente
    for q in questions:
        assert q['approved'] is False, "Una pregunta IA no debe nacer aprobada sin revisión docente"


def test_student_cannot_access_assessment_in_pending_review_state(client):
    """
    Un alumno intenta acceder a la evaluación de un tema cuya evaluación está en PENDING_REVIEW.
    El sistema debe denegar el acceso (403 NOT_PUBLISHED) para evitar que el alumno rinda preguntas sin validar.
    """
    # Topic 5 está en PENDING_REVIEW en los datos iniciales
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_lucas'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    response = client.get('/student/api/topics/5/evaluation')
    assert response.status_code == 403
    data = response.get_json()
    assert data['success'] is False
    assert data['status'] == 'NOT_PUBLISHED'
    assert 'revisada por el profesor' in data['error'].lower() or 'no ha sido publicada' in data['error'].lower()


def test_student_cannot_access_old_published_assessment_when_newer_one_is_pending(client, monkeypatch):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_lucas'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    from controllers import student_controller

    monkeypatch.setattr(student_controller, '_published_topic_for_student', lambda topic_id: {'id': topic_id, 'title': 'Tema del PPT'})
    monkeypatch.setattr(student_controller, 'fetch_assessments_for_topic', lambda topic_id: [
        {'id': 20, 'status': 'PENDING_REVIEW'},
        {'id': 19, 'status': 'PUBLISHED'},
    ])
    monkeypatch.setattr(student_controller, 'fetch_published_assessment_for_topic', lambda topic_id: {
        'id': 19,
        'status': 'PUBLISHED',
        'questions': [{'id': 1, 'question': 'Pregunta antigua', 'options': ['A', 'B'], 'answer': 'A', 'approved': True}],
    })

    response = client.get('/student/api/topics/5/evaluation')

    assert response.status_code == 403
    assert response.get_json()['status'] == 'NOT_PUBLISHED'


def test_teacher_can_edit_question_options_and_answer(client):
    """
    El profesor puede modificar el enunciado, opciones y respuesta correcta de una pregunta.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['teacher_id'] = 1
        sess['is_authenticated'] = True

    # Creamos una evaluación y pregunta
    aid = create_assessment(topic_id=3, title='Evaluación de Scratch', teacher_id=1, status='PENDING_REVIEW')
    qid = create_question(aid, '¿Qué es Scratch?', 'Un lenguaje visual', 'Un navegador', 'Un virus', 'Un lenguaje visual', approved=False)

    # El docente edita la pregunta
    edit_resp = client.put(f'/teacher/api/assessments/{aid}/questions/{qid}', json={
        'question': '¿Qué es Scratch en Computación?',
        'option_a': 'Un entorno visual de bloques',
        'option_b': 'Un sistema operativo',
        'option_c': 'Un tipo de teclado',
        'answer': 'Un entorno visual de bloques',
        'approved': True
    })

    assert edit_resp.status_code == 200
    assert edit_resp.get_json()['success'] is True

    # Verificar lectura
    assessment = fetch_assessment_by_id(aid)
    updated_q = next((q for q in assessment['questions'] if q['id'] == qid), None)
    assert updated_q is not None
    assert updated_q['question'] == '¿Qué es Scratch en Computación?'
    assert updated_q['option_a'] == 'Un entorno visual de bloques'
    assert updated_q['approved'] is True


def test_teacher_can_delete_unsuitable_question(client):
    """
    El profesor puede descartar/eliminar una pregunta generada por la IA que no cumpla con los estándares.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['teacher_id'] = 1
        sess['is_authenticated'] = True

    aid = create_assessment(topic_id=3, title='Evaluación Algoritmos', teacher_id=1, status='PENDING_REVIEW')
    qid1 = create_question(aid, 'Pregunta buena', 'A', 'B', 'C', 'A', approved=True)
    qid2 = create_question(aid, 'Pregunta confusa o errónea', 'X', 'Y', 'Z', 'X', approved=False)

    # Eliminar la segunda pregunta
    del_resp = client.delete(f'/teacher/api/assessments/{aid}/questions/{qid2}')
    assert del_resp.status_code == 200
    assert del_resp.get_json()['success'] is True

    assessment = fetch_assessment_by_id(aid)
    q_ids = [q['id'] for q in assessment['questions']]
    assert qid1 in q_ids
    assert qid2 not in q_ids


def test_full_lifecycle_generated_pending_approved_published(client):
    """
    Prueba el ciclo de vida completo:
    GENERATED -> PENDING_REVIEW -> APPROVED -> PUBLISHED
    Y comprueba que el alumno finalmente accede y solo recibe preguntas aprobadas.
    """
    teacher_sess = {
        'user': 'profesor',
        'user_role': 'teacher',
        'teacher_id': 1,
        'is_authenticated': True
    }
    student_sess = {
        'user': 'alumno_juan',
        'user_role': 'student',
        'student_id': 1,
        'user_grade': 5,
        'is_authenticated': True
    }

    # 1. Crear evaluación para topic 6
    aid = create_assessment(topic_id=6, title='Evaluación de Seguridad Digital', teacher_id=1, status='GENERATED')
    update_assessment_status(aid, 'PENDING_REVIEW')

    # Agregar dos preguntas: una aprobada por docente y otra desaprobada/rechazada
    q_ok = create_question(aid, '¿Cómo proteger contraseñas?', 'No compartirlas', 'Escribirlas en la pared', 'Decirlas en voz alta', 'No compartirlas', approved=True)
    q_bad = create_question(aid, 'Pregunta no aprobada', 'Op1', 'Op2', 'Op3', 'Op1', approved=False)

    # 2. Alumno intenta entrar -> debe ser 403 NOT_PUBLISHED
    with client.session_transaction() as sess:
        sess.update(student_sess)
    resp_student_blocked = client.get('/student/api/topics/6/evaluation')
    assert resp_student_blocked.status_code == 403
    assert resp_student_blocked.get_json()['status'] == 'NOT_PUBLISHED'

    # 3. Profesor aprueba la evaluación -> APPROVED
    with client.session_transaction() as sess:
        sess.update(teacher_sess)
    resp_approve = client.post(f'/teacher/api/assessments/{aid}/approve')
    assert resp_approve.status_code == 200
    assert resp_approve.get_json()['status'] == 'APPROVED'

    # Alumno sigue bloqueado porque está APPROVED pero aún no PUBLISHED
    with client.session_transaction() as sess:
        sess.update(student_sess)
    resp_still_blocked = client.get('/student/api/topics/6/evaluation')
    assert resp_still_blocked.status_code == 403

    # 4. Profesor publica la evaluación -> PUBLISHED
    with client.session_transaction() as sess:
        sess.update(teacher_sess)
    resp_publish = client.post(f'/teacher/api/assessments/{aid}/publish')
    assert resp_publish.status_code == 200
    assert resp_publish.get_json()['status'] == 'PUBLISHED'

    # 5. Alumno ahora sí puede acceder a la evaluación publicada
    with client.session_transaction() as sess:
        sess.update(student_sess)
    resp_student_ok = client.get('/student/api/topics/6/evaluation')
    assert resp_student_ok.status_code == 200
    payload = resp_student_ok.get_json()
    assert payload['success'] is True
    assert payload['status'] == 'PUBLISHED'
    assert 'evaluation' in payload

    received_questions = payload['evaluation']['questions']
    assert len(received_questions) >= 1
    # REGLA ESTRICTA: Todas las preguntas entregadas al alumno deben ser approved = True
    for q in received_questions:
        assert q['approved'] is True


def test_teacher_can_publish_assessment_with_fewer_than_fifteen_questions(client):
    teacher_session = {
        'user': 'profesor',
        'user_role': 'teacher',
        'teacher_id': 1,
        'is_authenticated': True,
    }
    student_session = {
        'user': 'alumno_juan',
        'user_role': 'student',
        'student_id': 1,
        'user_grade': 5,
        'is_authenticated': True,
    }

    assessment_id = create_assessment(
        topic_id=6,
        title='Evaluación corta de Seguridad Digital',
        teacher_id=1,
        status='PENDING_REVIEW',
    )
    question_id = create_question(
        assessment_id,
        '¿Cómo protegemos una contraseña?',
        'No compartirla',
        'Publicarla',
        'Usar la misma en todo',
        'No compartirla',
        approved=False,
    )

    with client.session_transaction() as sess:
        sess.update(teacher_session)
    approve_response = client.post(f'/teacher/api/assessments/{assessment_id}/approve')
    assert approve_response.status_code == 200
    assert approve_response.get_json()['status'] == 'APPROVED'
    assert fetch_assessment_by_id(assessment_id)['questions'][0]['approved'] is True

    publish_response = client.post(f'/teacher/api/assessments/{assessment_id}/publish')
    assert publish_response.status_code == 200
    assert publish_response.get_json()['status'] == 'PUBLISHED'

    with client.session_transaction() as sess:
        sess.update(student_session)
    get_response = client.get('/student/api/topics/6/evaluation')
    assert get_response.status_code == 200
    evaluation = get_response.get_json()['evaluation']
    assert evaluation['total_questions'] == 1
    assert evaluation['questions'][0]['id'] == question_id

    submit_response = client.post('/student/api/topics/6/evaluation', json={
        'answers': {'0': 'No compartirla'},
        'attempt_id': evaluation['attempt_id'],
        'started_at': datetime.now(timezone.utc).isoformat(),
        'time_spent': 30,
    })
    assert submit_response.status_code == 200
    result = submit_response.get_json()['result']
    assert result['total_questions'] == 1
    assert result['correct_answers'] == 1
    assert result['percentage'] == 100.0
    assert result['score'] == 20.0
