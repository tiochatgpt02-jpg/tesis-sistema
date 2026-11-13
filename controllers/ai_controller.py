import json

from flask import Blueprint, jsonify, render_template, session

from services.ai_service import check_ollama_status, generate_topic_learning_pack
from services.db_service import create_topic_evaluation, create_topic_game, fetch_game_by_id, fetch_topic_by_id, replace_topic_games

ai_blueprint = Blueprint('ai', __name__, url_prefix='/ai')


def _teacher_only():
    if session.get('user_role') != 'teacher' or not session.get('is_authenticated'):
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    return None


@ai_blueprint.route('/status', methods=['GET'])
def ollama_status():
    return jsonify(check_ollama_status())


@ai_blueprint.route('/generar-juego/<int:topic_id>', methods=['POST'])
def generar_juego_api(topic_id):
    denied = _teacher_only()
    if denied:
        return denied

    topic = fetch_topic_by_id(topic_id)
    if not topic:
        return jsonify({'success': False, 'error': 'Tema no encontrado'}), 404

    result = generate_topic_learning_pack(topic['title'], int(topic.get('grade') or 5))
    if not result.get('success'):
        return jsonify(result), 500

    juego = result['juego']
    preguntas = result.get('preguntas') or []
    replace_topic_games(topic_id)
    game_id = create_topic_game(
        topic_id,
        juego['titulo'],
        juego['instrucciones'],
        json.dumps(juego, ensure_ascii=False),
    )
    evaluation_id = None
    if preguntas:
        evaluation_id = create_topic_evaluation(topic_id, 'media', preguntas)
    return jsonify({
        'success': True,
        'game_id': game_id,
        'evaluation_id': evaluation_id,
        'source': result.get('source', 'ollama'),
        'aviso': result.get('aviso'),
        'juego': juego,
        'preguntas': preguntas,
        'mensaje': 'Juego y preguntas generados. El alumno los verá en Juegos y Evaluaciones.',
    }), 201


@ai_blueprint.route('/juego/<int:game_id>', methods=['GET'])
def ver_juego_view(game_id):
    game = fetch_game_by_id(game_id)
    if not game or not game.get('pares'):
        return 'Juego no encontrado o sin contenido generado.', 404
    return render_template('student_juegos.html', juego_json=game)


@ai_blueprint.route('/juego/<int:game_id>/json', methods=['GET'])
def ver_juego_json(game_id):
    game = fetch_game_by_id(game_id)
    if not game or not game.get('pares'):
        return jsonify({'success': False, 'error': 'Juego no encontrado'}), 404
    return jsonify({'success': True, 'juego': game})
