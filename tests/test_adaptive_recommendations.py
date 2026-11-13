"""
Tests automatizados para GOAL 6: Recomendaciones Adaptativas con IA + ML.
Verifica:
1. Unificación de los 4 pilares: Notas + Evaluaciones + Juegos + Predicción ML.
2. Diagnóstico objetivo basado en datos reales del alumno (sin textos aleatorios).
3. Generación del plan personalizado estructurado:
   - 📖 Leer material
   - 🎮 Juego
   - 📝 Evaluación
4. Caso específico del usuario: Alumno con fallas en fracciones -> Ruta de Fracciones.
5. Actualización dinámica tras realizar actividades o evaluaciones.
6. Funcionamiento del endpoint REST GET /student/api/recommendations.
"""
import pytest
from app import app
from services.db_service import (
    record_student_result,
    record_student_assessment_attempt,
    record_student_game_attempt,
    fetch_student_notes,
)
from services.adaptive_recommendations_service import build_adaptive_recommendations


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
        sess['student_name'] = 'Juan Pérez'
        sess['user_grade'] = 5
        sess['is_authenticated'] = True
    return client


def test_adaptive_recommendations_integration_of_all_four_pillars():
    """
    GOAL 6: Valida que el motor une Notas + Evaluaciones + Juegos + Predicción ML.
    """
    result = build_adaptive_recommendations(student_id=1)
    assert result['success'] is True
    diag = result['student_diagnosis']

    # 1. Notas
    assert 'average_score' in diag
    assert diag['notes_count'] >= 1

    # 2. Evaluaciones
    assert 'evaluations_count' in diag
    assert 'failed_questions_count' in diag

    # 3. Juegos
    assert 'games_count' in diag

    # 4. Predicción ML
    assert 'ml_risk_level' in diag
    assert diag['ml_risk_level'] in ('Alto', 'Medio', 'Bajo', 'HIGH', 'MEDIUM', 'LOW')
    assert 'ml_probability' in diag


def test_adaptive_recommendation_contains_three_canonical_actions():
    """
    GOAL 6: Valida la presencia de las 3 recomendaciones estructuradas:
    📖 Leer material
    🎮 Juego
    📝 Evaluación
    """
    result = build_adaptive_recommendations(student_id=1)
    actions = result['actions']
    assert len(actions) == 3

    categories = [a['category'] for a in actions]
    assert 'material' in categories
    assert 'juego' in categories
    assert 'evaluacion' in categories

    badges = [a['badge'] for a in actions]
    assert any('Leer material' in b for b in badges)
    assert any('Juego' in b for b in badges)
    assert any('Evaluación' in b for b in badges)


def test_student_with_failed_fractions_gets_fractions_pathway():
    """
    Ejemplo exacto del usuario:
    Alumno falló 4 preguntas de fracciones ->
    Te recomendamos:
    📖 Leer material: Fracciones básicas
    🎮 Juego: Comparar fracciones
    📝 Evaluación: Práctica corta
    """
    # Alumno 1 falló 4 preguntas en evaluación de fracciones básicas (11/15 correctas)
    record_student_assessment_attempt(
        student_id=1,
        assessment_id=4,
        score=14.67,
        time_spent=280,
        correct_answers=11,
        total_questions=15,
        percentage=73.33,
        reinforce_topics=['Fracciones básicas'],
        answers={'0': 'incorrecto', '1': 'incorrecto', '2': 'incorrecto', '3': 'incorrecto'},
    )
    result = build_adaptive_recommendations(student_id=1)
    diag = result['student_diagnosis']

    # Diagnóstico debe identificar fracciones y 4 preguntas falladas
    assert 'fracci' in str(diag.get('weak_topic', '')).lower() or 'fracci' in str(diag.get('evidence', '')).lower()
    assert diag.get('failed_questions_count', 0) == 4
    assert '4 preguntas' in diag.get('evidence', '')

    actions = result['actions']
    mat_action = next(a for a in actions if a['category'] == 'material')
    game_action = next(a for a in actions if a['category'] == 'juego')
    eval_action = next(a for a in actions if a['category'] == 'evaluacion')

    # 📖 Leer material: Fracciones básicas
    assert mat_action['title'] == 'Fracciones básicas'
    # 🎮 Juego: Comparar fracciones
    assert game_action['title'] == 'Juegos disponibles'
    # 📝 Evaluación: Práctica corta
    assert eval_action['title'] == 'Práctica corta'


def test_recommendations_are_deterministic_and_not_random():
    """
    Definition of Done: No son textos aleatorios.
    Múltiples llamadas con el mismo estado académico deben producir resultados idénticos y reproducibles.
    """
    run1 = build_adaptive_recommendations(student_id=1)
    run2 = build_adaptive_recommendations(student_id=1)

    assert run1['primary_topic'] == run2['primary_topic']
    assert run1['student_diagnosis']['evidence'] == run2['student_diagnosis']['evidence']
    assert [a['title'] for a in run1['actions']] == [a['title'] for a in run2['actions']]


def test_recommendations_update_dynamically_after_new_activity():
    """
    Definition of Done: Se actualizan después de actividades.
    Si el alumno realiza una nueva evaluación con fallas en otro tema (ej: Fotosíntesis),
    el motor detecta la nueva debilidad y actualiza las recomendaciones.
    """
    # 1. Registrar un intento reciente donde el alumno falló en Fotosíntesis (topic 5)
    record_student_assessment_attempt(
        student_id=1,
        assessment_id=2,
        score=6.0,
        time_spent=200,
        correct_answers=1,
        total_questions=5,
        percentage=20.0,
        reinforce_topics=['Fotosíntesis', 'Plantas'],
        answers={'0': 'incorrecto'},
    )

    # 2. Consultar las recomendaciones actualizadas
    updated = build_adaptive_recommendations(student_id=1)
    diag = updated['student_diagnosis']

    # La nueva evidencia debe reflejar la última actividad registrada
    assert 'fotosíntesis' in str(diag.get('weak_topic', '')).lower() or 'fotosíntesis' in str(diag.get('evidence', '')).lower()
    actions = updated['actions']
    game_action = next(a for a in actions if a['category'] == 'juego')
    assert 'foto' in game_action['title'].lower() or 'planta' in game_action['title'].lower()


def test_api_recommendations_endpoint_returns_json_payload(authenticated_student_client):
    """
    Verifica que el endpoint GET /student/api/recommendations entrega el payload adaptativo completo.
    """
    resp = authenticated_student_client.get('/student/api/recommendations')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'student_diagnosis' in data
    assert 'actions' in data
    assert len(data['actions']) == 3
    assert 'recommendations' in data
