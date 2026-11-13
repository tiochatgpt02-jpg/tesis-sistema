import pytest
from app import app
from services.ai_service import generate_questions_from_teacher_material
from services.db_service import fetch_all_materials_for_student, get_presentations_for_topic


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    with app.test_client() as client:
        yield client


def test_teacher_can_create_material_associated_with_topic(client):
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['is_authenticated'] = True

    response = client.post('/teacher/api/topic/1/materials', json={
        'title': 'Fotosíntesis y Energía',
        'content': 'Las plantas producen energía y oxígeno mediante la fotosíntesis utilizando luz solar y agua.',
        'topic_id': 1
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'material_id' in data
    assert data['topic_id'] == 1


def test_material_creation_requires_title_and_content(client):
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['is_authenticated'] = True

    # Missing title
    resp1 = client.post('/teacher/api/topic/1/materials', json={
        'title': '',
        'content': 'Texto sin título'
    })
    assert resp1.status_code == 400

    # Missing content
    resp2 = client.post('/teacher/api/topic/1/materials', json={
        'title': 'Título sin contenido',
        'content': ''
    })
    assert resp2.status_code == 400


def test_student_can_view_published_materials(client):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    # Check API list
    resp = client.get('/student/api/materials')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert isinstance(data['materials'], list)
    assert len(data['materials']) > 0

    # Check that material has title, topic_title and snippet
    mat = data['materials'][0]
    assert 'title' in mat
    assert 'topic_title' in mat
    assert 'snippet' in mat

    # Check single material endpoint
    mat_id = mat['id']
    single_resp = client.get(f'/student/api/materials/{mat_id}')
    assert single_resp.status_code == 200
    single_data = single_resp.get_json()
    assert single_data['success'] is True
    assert single_data['material']['id'] == mat_id
    assert 'content' in single_data['material']


def test_ai_generates_questions_grounded_strictly_in_teacher_text():
    teacher_text = (
        "Las plantas producen glucosa y oxígeno mediante la fotosíntesis. "
        "Para realizar este proceso absorben agua del suelo a través de sus raíces. "
        "La clorofila es el pigmento verde que capta la energía de la luz solar."
    )
    title = "Fotosíntesis"

    result = generate_questions_from_teacher_material(teacher_text, title, grade=5)

    assert result['success'] is True
    assert result['material_title'] == title
    questions = result['questions']
    assert len(questions) >= 2

    # Verificar que las preguntas están fundamentadas con fragmentos de referencia extraídos del texto
    for q in questions:
        assert 'question' in q and len(q['question']) > 5
        assert 'options' in q and len(q['options']) >= 2
        assert 'answer' in q
        assert q['answer'] in q['options']
        # El fragmento de referencia debe estar contenido o extraído del texto original
        ref = q.get('reference_fragment')
        assert ref is not None
        assert any(word.lower() in teacher_text.lower() for word in ref.split() if len(word) > 4)


def test_student_practice_and_grading_flow(client):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    # 1. Obtener práctica de un material
    practice_resp = client.get('/student/api/materials/1/practice')
    assert practice_resp.status_code == 200
    practice_data = practice_resp.get_json()
    assert practice_data['success'] is True
    questions = practice_data['questions']
    assert len(questions) > 0

    from services.learning_attempt_service import _attempts
    keys = _attempts[practice_data['attempt_id']]['questions']
    # 2. Enviar respuestas correctas
    answers = {}
    for idx, q in enumerate(questions):
        answers[str(idx)] = keys[idx]['answer']

    submit_resp = client.post('/student/api/materials/1/practice', json={
        'answers': answers,
        'attempt_id': practice_data['attempt_id']
    })
    assert submit_resp.status_code == 200
    submit_data = submit_resp.get_json()
    assert submit_data['success'] is True
    assert submit_data['score_20'] > 0
    assert submit_data['correct_count'] == len(questions)

    # 3. Marcar explícitamente como revisado
    rev_resp = client.post('/student/api/materials/1/reviewed')
    assert rev_resp.status_code == 200
    assert rev_resp.get_json()['success'] is True


def test_opening_material_does_not_mark_it_as_read_until_read_is_confirmed(client):
    with client.session_transaction() as sess:
        sess['user'] = 'profesor'
        sess['user_role'] = 'teacher'
        sess['is_authenticated'] = True

    create_resp = client.post('/teacher/api/topic/4/materials', json={
        'title': 'Material de prueba para lectura',
        'content': 'Este texto se usa para verificar que al abrir el material se marque como leído.',
        'topic_id': 4,
    })
    assert create_resp.status_code == 201
    material_id = create_resp.get_json()['material_id']
    assert create_resp.get_json()['status'] == 'DRAFT'

    publish_resp = client.post(f'/teacher/api/materials/{material_id}/publish')
    assert publish_resp.status_code == 200
    assert publish_resp.get_json()['status'] == 'PUBLISHED'

    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    open_resp = client.get(f"/student/api/materials/{material_id}")
    assert open_resp.status_code == 200
    open_data = open_resp.get_json()
    assert open_data['success'] is True
    assert open_data['material'].get('reviewed') is not True

    updated_resp = client.get('/student/api/materials')
    updated_material = next(item for item in updated_resp.get_json()['materials'] if item['id'] == material_id)
    assert updated_material['reviewed'] is not True

    mark_resp = client.post(f'/student/api/materials/{material_id}/reviewed')
    assert mark_resp.status_code == 200
    updated_resp = client.get('/student/api/materials')
    updated_material = next(item for item in updated_resp.get_json()['materials'] if item['id'] == material_id)
    assert updated_material['reviewed'] is True


def test_teacher_uploaded_presentations_appear_for_students(client):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    resp = client.get('/student/api/materials')
    assert resp.status_code == 200
    material_titles = [item['title'] for item in resp.get_json()['materials']]
    assert any('Guía de fracciones básicas' in title for title in material_titles)
    assert any('Presentación de operaciones' in title for title in material_titles)


def test_fetch_all_materials_for_student_includes_teacher_presentations():
    materials = fetch_all_materials_for_student(1, 5)
    presentation_titles = [item['title'] for item in get_presentations_for_topic(4)]

    assert any(title in [item['title'] for item in materials] for title in presentation_titles)


def test_student_dashboard_shows_topic_material_panel_without_duplicate_material_grid(client):
    with client.session_transaction() as sess:
        sess['user'] = 'alumno_juan'
        sess['user_role'] = 'student'
        sess['student_id'] = 1
        sess['user_grade'] = 5
        sess['is_authenticated'] = True

    resp = client.get('/student/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Mis <span>Materiales Educativos</span>" not in html
    assert "student-materials-grid" not in html
    assert "Actividades del tema seleccionado" in html
    assert "selected-activity-view" in html
    assert "modalReadMaterial" in html
    assert "material-practice-area" in html
