from app import app
from services.db_service import create_ai_generated_game, fetch_ai_generated_game_by_id


def test_editing_published_game_requires_approval_again():
    content = {'statement': 'El teclado permite escribir.', 'correct_answer': True, 'explanation': 'El teclado es un dispositivo de entrada.'}
    identity = create_ai_generated_game(topic_id=1, game_type='true_false', title='Uso del teclado',
                                        instruction='Decide si la afirmación es correcta.', content_json=content,
                                        status='PUBLISHED', created_by=1)
    with app.test_client() as client:
        with client.session_transaction() as session:
            session.update(user='teacher', user_role='teacher', is_authenticated=True, user_id=1)
        response = client.put(f'/teacher/api/ai-games/{identity}', json={'title': 'Teclado y escritura', 'content_json': content})
        assert response.status_code == 200
        assert response.get_json()['game']['status'] == 'PENDING_REVIEW'
        assert fetch_ai_generated_game_by_id(identity)['title'] == 'Teclado y escritura'
        assert client.post(f'/teacher/api/ai-games/{identity}/publish').status_code == 409


def test_student_cannot_edit_a_game():
    with app.test_client() as client:
        with client.session_transaction() as session:
            session.update(user='student', user_role='student', is_authenticated=True, user_id=1)
        response = client.put('/teacher/api/ai-games/1', json={'title': 'Changed'})
        assert response.status_code in (302, 401, 403)
