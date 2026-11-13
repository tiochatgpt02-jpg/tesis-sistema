import io
import os
import json
import zipfile
import pytest
from app import app
from config import Config
from services.material_extractor_service import MaterialExtractorService
from services.game_validation_service import GameValidationService
from services.ai_game_generator_service import AIGameGeneratorService
from services.game_engine import GameEngine
from services.db_service import (
    create_ai_generated_game,
    fetch_ai_generated_games,
    fetch_ai_generated_game_by_id,
    update_ai_generated_game,
    update_ai_generated_game_status,
    delete_ai_generated_game,
    fetch_published_ai_games_for_topic,
    record_student_ai_game_attempt,
    fetch_student_game_attempts,
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
        with client.session_transaction() as sess:
            sess['is_authenticated'] = True
            sess['user'] = 'profesor1'
            sess['user_id'] = 1
            sess['user_role'] = 'teacher'
            sess['student_id'] = 1
        yield client


# =========================================================================
# 1. Pruebas de MaterialExtractorService
# =========================================================================

def test_material_extractor_from_text():
    sample_text = """
    # Las Plantas y la Fotosíntesis
    Las plantas fabrican su propio alimento mediante la fotosíntesis.
    - Utilizan la energía de la luz solar y el agua absorbida por las raíces.
    - La clorofila es el pigmento verde encargado de captar la luz del sol.
    - Durante el proceso expulsan oxígeno que beneficia a los seres vivos.
    """
    extracted = MaterialExtractorService.extract_from_text(sample_text, title="Fotosíntesis")
    assert extracted['source_type'] == 'text'
    assert extracted['title'] == "Fotosíntesis"
    assert len(extracted['key_points']) >= 2
    assert "fotosíntesis" in extracted['raw_text'].lower()
    assert extracted['learning_summary']['topic'] == 'Fotosíntesis'
    assert extracted['learning_summary']['concepts']


def test_material_extractor_from_pptx(tmp_path):
    # Generar un archivo PPTX mínimo en memoria para probar la extracción con zipfile + xml nativo
    pptx_path = tmp_path / "test_presentation.pptx"
    slide1_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:nvSpPr><p:cNvPr id="1" name="Title"/><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
                    <p:txBody><a:p><a:t>El Sistema Solar y los Planetas</a:t></a:p></p:txBody>
                </p:sp>
                <p:sp>
                    <p:nvSpPr><p:cNvPr id="2" name="Body"/><p:nvPr/></p:nvSpPr>
                    <p:txBody>
                        <a:p><a:t>La Tierra gira alrededor del Sol en 365 días.</a:t></a:p>
                        <a:p><a:t>La Luna es el satélite natural de la Tierra.</a:t></a:p>
                    </p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:sld>"""

    notes1_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:txBody><a:p><a:t>Recordar a los alumnos que el Sol es una estrella amarilla.</a:t></a:p></p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:notes>"""

    with zipfile.ZipFile(pptx_path, 'w') as zf:
        zf.writestr('ppt/slides/slide1.xml', slide1_xml)
        zf.writestr('ppt/notesSlides/notesSlide1.xml', notes1_xml)

    extracted = MaterialExtractorService.extract_from_pptx(str(pptx_path))
    assert extracted['source_type'] == 'pptx'
    assert "El Sistema Solar" in extracted['title']
    assert len(extracted['key_points']) >= 1
    assert extracted['slides_count'] == 1
    assert extracted['speaker_notes_count'] == 1
    assert "estrella amarilla" in extracted['raw_text']


# =========================================================================
# 2. Pruebas de GameValidationService
# =========================================================================

def test_game_validation_service_multiple_choice():
    valid_game = {
        'game_type': 'multiple_choice',
        'title': 'El Sol y los Planetas',
        'instruction': 'Selecciona la respuesta correcta.',
        'content': {
            'question': '¿Qué es el Sol?',
            'options': ['Una estrella', 'Un planeta', 'Un satélite'],
            'answer': 'Una estrella',
            'explanation': 'El sol es la estrella en el centro del sistema solar.'
        }
    }
    is_valid, err, cleaned = GameValidationService.validate(valid_game)
    assert is_valid is True
    assert cleaned['game_type'] == 'multiple_choice'
    assert cleaned['content']['answer'] == 'Una estrella'

    # Inválido: opciones insuficientes
    invalid_game = {
        'game_type': 'multiple_choice',
        'title': 'Test',
        'instruction': 'Test',
        'content': {'question': '¿Pregunta?', 'options': ['Solo una'], 'answer': 'Solo una'}
    }
    is_valid, err, _ = GameValidationService.validate(invalid_game)
    assert is_valid is False
    assert "al menos 2 opciones" in err


def test_game_validation_service_all_types():
    # True/False
    tf_game = {
        'game_type': 'true_false',
        'title': 'Gravedad en la Tierra',
        'instruction': 'Indica si es verdadero o falso.',
        'content': {
            'statement': 'La gravedad atrae los objetos hacia el centro de la Tierra.',
            'correct_answer': True,
            'explanation': 'La gravedad es la fuerza de atracción que nos mantiene en el suelo.'
        }
    }
    is_valid, _, cleaned = GameValidationService.validate(tf_game)
    assert is_valid is True
    assert cleaned['content']['correct_answer'] is True

    # Fill Blank
    fb_game = {
        'game_type': 'fill_blank',
        'title': 'Fotosíntesis y Clorofila',
        'instruction': 'Completa la oración.',
        'content': {
            'sentence': 'Las plantas capturan luz solar mediante la ______ presente en las hojas.',
            'blank_word': 'clorofila',
            'options': ['clorofila', 'arena', 'gasolina'],
            'explanation': 'La clorofila es el pigmento verde de las plantas.'
        }
    }
    is_valid, _, cleaned = GameValidationService.validate(fb_game)
    assert is_valid is True
    assert cleaned['content']['blank_word'] == 'clorofila'

    # Matching
    match_game = {
        'game_type': 'matching',
        'title': 'Parejas Científicas',
        'instruction': 'Une los conceptos.',
        'content': {
            'pairs': [
                {'left': 'Sol', 'right': 'Estrella central'},
                {'left': 'Tierra', 'right': 'Planeta donde vivimos'}
            ],
            'explanation': '¡Excelente trabajo uniendo conceptos!'
        }
    }
    is_valid, _, cleaned = GameValidationService.validate(match_game)
    assert is_valid is True
    assert len(cleaned['content']['pairs']) == 2


# =========================================================================
# 3. Pruebas de AIGameGeneratorService y Fallback Offline
# =========================================================================

def test_ai_game_generator_offline_fallback():
    material = {
        'title': 'Ecosistemas y Seres Vivos',
        'raw_text': 'Los ecosistemas están formados por factores bióticos y abióticos. Las plantas son productores primarios.',
        'key_points': ['Factores bióticos', 'Productores primarios']
    }

    # Probar que todos los tipos generan estructuras válidas sin Ollama
    for gtype in ['multiple_choice', 'true_false', 'fill_blank', 'matching']:
        res = AIGameGeneratorService.generate_game(material, game_type=gtype, grade=5)
        assert res['success'] is True
        assert res['game']['game_type'] == gtype
        assert res['game']['learning_objective']
        assert res['game']['content_reference']
        is_valid, _, _ = GameValidationService.validate(res['game'])
        assert is_valid is True


def test_offline_matching_uses_presentation_sections_instead_of_cover_labels(monkeypatch):
    material = {
        'title': 'El ciclo del agua',
        'raw_text': (
            '# El ciclo del agua\n'
            '- Material de Ciencias Naturales para primaria\n'
            '# Evaporación\n'
            '- El calor del Sol calienta el agua de mares, ríos y lagos.\n'
            '# Condensación\n'
            '- En las zonas altas, el vapor de agua se enfría.\n'
            '# Precipitación\n'
            '- Cuando las gotas de una nube pesan mucho, caen como lluvia.\n'
        ),
        'key_points': ['Material de Ciencias Naturales para primaria', 'ETAPA 1'],
    }

    monkeypatch.setattr(
        AIGameGeneratorService,
        '_call_ollama',
        classmethod(lambda cls, prompt, timeout=120: (_ for _ in ()).throw(RuntimeError('sin modelo'))),
    )
    generated = AIGameGeneratorService.generate_game(material, game_type='matching', grade=5)
    pairs = generated['game']['content']['pairs']

    assert [pair['left'] for pair in pairs] == ['Evaporación', 'Condensación', 'Precipitación']
    assert all(pair['right'].replace('…', '') in material['raw_text'] for pair in pairs)
    assert generated['game']['learning_objective'] == 'Evaporación'


def test_game_engine_supports_memory_ordering_drag_drop_and_challenge_offline():
    material = {
        'title': 'Ciclo de una Planta',
        'raw_text': 'La semilla germina. Luego nace una planta. Después aparece la flor y finalmente se forma el fruto.',
        'key_points': ['La semilla germina primero', 'La planta crece después', 'La flor aparece más tarde', 'El fruto se forma al final'],
    }
    for game_type in ('memory', 'ordering', 'drag_drop', 'challenge'):
        generated = AIGameGeneratorService.generate_game(material, game_type=game_type, grade=4)
        assert generated['success'] is True
        valid, error, normalized = GameValidationService.validate(generated['game'])
        assert valid, error
        assert normalized['game_type'] == game_type


def test_validation_rejects_html_and_preserves_gamification_contract():
    game = {
        'game_type': 'memory',
        'title': 'Memoria de Plantas',
        'difficulty': 'easy',
        'learning_objective': 'Relacionar conceptos de las plantas',
        'content_reference': 'Material: Las plantas',
        'feedback_correct': '¡Excelente explorador!',
        'feedback_wrong': '¡Casi! Busca otra pista.',
        'content': {'pairs': [{'left': 'Raíz', 'right': 'Absorbe agua'}, {'left': 'Hoja', 'right': 'Capta luz'}]},
    }
    valid, error, normalized = GameValidationService.validate(game)
    assert valid, error
    assert normalized['difficulty'] == 'easy'
    assert normalized['learning_objective'] == game['learning_objective']

    game['title'] = '<strong>Juego</strong>'
    valid, error, _ = GameValidationService.validate(game)
    assert not valid
    assert 'HTML' in error


def test_game_engine_scores_new_game_types():
    assert GameEngine.score_attempt('ordering', {'items': ['Semilla', 'Planta', 'Flor']}, {'order': ['Semilla', 'Planta', 'Flor']}) == (True, 1.0)
    is_correct, ratio = GameEngine.score_attempt(
        'drag_drop',
        {'items': [{'item': 'Perro', 'category': 'Mamíferos'}, {'item': 'Águila', 'category': 'Aves'}]},
        {'placements': [{'item': 'Perro', 'category': 'Mamíferos'}, {'item': 'Águila', 'category': 'Aves'}]},
    )
    assert is_correct is True and ratio == 1.0


@pytest.mark.parametrize(('game_type', 'content', 'payload'), [
    ('memory', {'pairs': [{'left': 'Raíz', 'right': 'Absorbe agua'}, {'left': 'Hoja', 'right': 'Capta luz'}]}, {'matches': [{'left': 'Raíz', 'right': 'Absorbe agua'}, {'left': 'Hoja', 'right': 'Capta luz'}]}),
    ('ordering', {'items': ['Semilla', 'Planta', 'Flor']}, {'order': ['Semilla', 'Planta', 'Flor']}),
    ('drag_drop', {'categories': ['Aves', 'Mamíferos'], 'items': [{'item': 'Águila', 'category': 'Aves'}, {'item': 'Perro', 'category': 'Mamíferos'}]}, {'placements': [{'item': 'Águila', 'category': 'Aves'}, {'item': 'Perro', 'category': 'Mamíferos'}]}),
    ('challenge', {'levels': [{'level': 1, 'question': '¿A?', 'options': ['A', 'B'], 'answer': 'A'}, {'level': 2, 'question': '¿B?', 'options': ['B', 'C'], 'answer': 'B'}, {'level': 3, 'question': '¿C?', 'options': ['C', 'D'], 'answer': 'C'}]}, {'answers': ['A', 'B', 'C']}),
])
def test_student_can_complete_each_new_published_game(client, game_type, content, payload):
    game_id = create_ai_generated_game(
        topic_id=4,
        game_type=game_type,
        title=f'Juego {game_type}',
        instruction='Completa la misión.',
        content_json=content,
        status='PUBLISHED',
        created_by=1,
    )
    with client.session_transaction() as sess:
        sess['user_role'] = 'student'
        sess['student_id'] = 1
    response = client.post(f'/student/api/ai-games/{game_id}/play', json={'time_spent': 3, **payload})
    assert response.status_code == 200
    assert response.get_json()['is_correct'] is True
    delete_ai_generated_game(game_id)
    is_correct, ratio = GameEngine.score_attempt(
        'challenge',
        {'levels': [{'answer': 'A'}, {'answer': 'B'}, {'answer': 'C'}]},
        {'answers': ['A', 'B', 'C']},
    )
    assert is_correct is True and ratio == 1.0


# =========================================================================
# 4. Pruebas de Base de Datos y Persistencia
# =========================================================================

def test_db_ai_generated_games_crud():
    game_id = create_ai_generated_game(
        topic_id=4,
        game_type='multiple_choice',
        title='Juego de Prueba DB',
        instruction='Prueba de base de datos',
        content_json={'question': '¿2+2?', 'options': ['4', '5'], 'answer': '4'},
        status='PENDING_REVIEW',
        created_by=1
    )
    assert game_id > 0

    game = fetch_ai_generated_game_by_id(game_id)
    assert game is not None
    assert game['title'] == 'Juego de Prueba DB'
    assert game['status'] == 'PENDING_REVIEW'

    # Actualizar estado a APPROVED y PUBLISHED
    update_ai_generated_game_status(game_id, 'APPROVED')
    assert fetch_ai_generated_game_by_id(game_id)['status'] == 'APPROVED'

    update_ai_generated_game_status(game_id, 'PUBLISHED')
    assert fetch_ai_generated_game_by_id(game_id)['status'] == 'PUBLISHED'

    # Debe figurar en los publicados para el tema 4
    published = fetch_published_ai_games_for_topic(4)
    assert any(g['id'] == game_id for g in published)

    # Eliminar
    delete_ai_generated_game(game_id)
    assert fetch_ai_generated_game_by_id(game_id) is None


# =========================================================================
# 5. Flujo Completo Docente: Generación -> Aprobación -> Publicación
# =========================================================================

def test_teacher_generate_and_approval_workflow(client):
    # Generar juego desde material
    resp = client.post('/teacher/api/materials/1/generate-game', json={'game_type': 'multiple_choice'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['success'] is True
    game_id = data['game_id']
    assert data['status'] == 'PENDING_REVIEW'

    # Verificar que el juego está en la lista de revisión docente
    list_resp = client.get('/teacher/api/ai-games?status=PENDING_REVIEW')
    assert list_resp.status_code == 200
    games = list_resp.get_json()['games']
    assert any(g['id'] == game_id for g in games)

    # El docente edita el juego
    edit_resp = client.put(f'/teacher/api/ai-games/{game_id}', json={
        'title': 'Fracciones Mágicas Editadas',
        'instruction': 'Elige la respuesta correcta.',
        'content_json': {
            'question': '¿Qué es el denominador?',
            'options': ['Total de partes iguales', 'Las partes que comemos'],
            'answer': 'Total de partes iguales',
            'explanation': 'El denominador indica en cuántas partes se dividió el entero.'
        }
    })
    assert edit_resp.status_code == 200
    assert edit_resp.get_json()['game']['title'] == 'Fracciones Mágicas Editadas'

    # El docente aprueba el juego
    approve_resp = client.post(f'/teacher/api/ai-games/{game_id}/approve')
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()['status'] == 'APPROVED'

    # El docente publica el juego para los alumnos
    publish_resp = client.post(f'/teacher/api/ai-games/{game_id}/publish')
    assert publish_resp.status_code == 200
    assert publish_resp.get_json()['status'] == 'PUBLISHED'

    # Regenerar recupera el material original y obliga una nueva revisión docente.
    with client.session_transaction() as sess:
        sess['user_role'] = 'teacher'
    regenerate_resp = client.post(f'/teacher/api/ai-games/{game_id}/regenerate', json={'difficulty': 'medium'})
    assert regenerate_resp.status_code == 200
    regenerated = regenerate_resp.get_json()['game']
    assert regenerated['status'] == 'PENDING_REVIEW'
    assert regenerated['content_json']['_meta']['difficulty'] == 'medium'


# =========================================================================
# 6. Flujo del Alumno: Seguridad y Gameplay con UX Infantil (+10 puntos)
# =========================================================================

def test_student_cannot_see_unpublished_games(client):
    # Crear un juego en PENDING_REVIEW
    game_id = create_ai_generated_game(
        topic_id=4,
        game_type='multiple_choice',
        title='Juego Secreto Docente',
        instruction='No visible',
        content_json={'question': '¿Secreto?', 'options': ['Sí', 'No'], 'answer': 'Sí'},
        status='PENDING_REVIEW',
        created_by=1
    )

    # Conectar como alumno
    with client.session_transaction() as sess:
        sess['user_role'] = 'student'
        sess['student_id'] = 1

    # El alumno consulta los juegos del tema 4
    resp = client.get('/student/api/topics/4/ai-games')
    assert resp.status_code == 200
    games = resp.get_json()['games']
    # El juego no publicado NUNCA debe aparecer
    assert not any(g['id'] == game_id for g in games)

    # Intento de jugar un juego no publicado debe responder 403
    play_resp = client.post(f'/student/api/ai-games/{game_id}/play', json={'answer': 'Sí'})
    assert play_resp.status_code == 403

    # Limpiar
    delete_ai_generated_game(game_id)


def test_student_gameplay_and_scoring(client):
    # Crear y publicar un juego
    game_id = create_ai_generated_game(
        topic_id=4,
        game_type='multiple_choice',
        title='Reto de Puntos de Fracciones',
        instruction='Responde para ganar puntos',
        content_json={
            'question': '¿En cuántas partes divide un medio (1/2) a la unidad?',
            'options': ['En 2 partes iguales', 'En 5 partes', 'En 10 partes'],
            'answer': 'En 2 partes iguales',
            'explanation': 'Un medio divide la unidad en dos partes exactamente iguales.'
        },
        status='PUBLISHED',
        created_by=1
    )

    with client.session_transaction() as sess:
        sess['user_role'] = 'student'
        sess['student_id'] = 1

    # 1. El alumno responde correctamente
    resp_correct = client.post(f'/student/api/ai-games/{game_id}/play', json={
        'answer': 'En 2 partes iguales',
        'time_spent': 8
    })
    assert resp_correct.status_code == 200
    data_c = resp_correct.get_json()
    assert data_c['success'] is True
    assert data_c['is_correct'] is True
    assert data_c['points_earned'] == 10
    assert "¡Correcto! 🎉 +10 puntos" in data_c['feedback_headline']

    # 2. El alumno responde incorrectamente
    resp_wrong = client.post(f'/student/api/ai-games/{game_id}/play', json={
        'answer': 'En 5 partes',
        'time_spent': 5
    })
    assert resp_wrong.status_code == 200
    data_w = resp_wrong.get_json()
    assert data_w['success'] is True
    assert data_w['is_correct'] is False
    assert data_w['points_earned'] == 0
    assert "¡Casi! Inténtalo de nuevo 💪" in data_w['feedback_headline']

    # 3. Verificar persistencia de intentos
    attempts = fetch_student_game_attempts(student_id=1, game_id=game_id)
    assert len(attempts) >= 2

    delete_ai_generated_game(game_id)
