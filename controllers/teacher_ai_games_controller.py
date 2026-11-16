from flask import Blueprint, jsonify, request, session
from config import Config
from services.material_extractor_service import MaterialExtractorService
from services.ai_game_generator_service import AIGameGeneratorService
from services.game_validation_service import GameValidationService
from services.adaptive_learning_service import build_adaptive_learning_profile
from services.adaptive_game_generator_service import AdaptiveGameGeneratorService
from services.db_service import (
    fetch_material_by_id,
    fetch_presentation_by_id,
    create_ai_generated_game,
    fetch_ai_generated_games,
    fetch_ai_generated_game_by_id,
    update_ai_generated_game,
    update_ai_generated_game_status,
    delete_ai_generated_game,
)

teacher_ai_games_blueprint = Blueprint('teacher_ai_games', __name__, url_prefix='/teacher')


def _content_with_metadata(game):
    """Mantiene el esquema gamificado sin requerir una migración destructiva de la BD."""
    content = dict(game.get('content') or {})
    content['_meta'] = {
        key: game.get(key, '')
        for key in ('description', 'subject', 'grade', 'difficulty', 'learning_objective', 'content_reference', 'feedback_correct', 'feedback_wrong')
    }
    return content


def _teacher_check():
    """Valida permisos docentes salvo en modo mock."""
    if not session.get('is_authenticated') or 'user' not in session:
        if not Config.USE_MOCK_DATA:
            return jsonify({'error': 'No autorizado', 'success': False}), 401
    if session.get('user_role') and session.get('user_role') != 'teacher':
        return jsonify({'error': 'Requiere permisos de profesor', 'success': False}), 403
    return None


def _extract_presentation_content(presentation):
    return MaterialExtractorService.extract_from_presentation_record(presentation)


@teacher_ai_games_blueprint.route('/api/students/<int:student_id>/adaptive-analysis', methods=['GET'])
def api_adaptive_student_analysis(student_id):
    """Vista docente de la evidencia usada antes de pedir una práctica adaptativa."""
    denied = _teacher_check()
    if denied:
        return denied
    return jsonify({'success': True, 'analysis': build_adaptive_learning_profile(student_id)}), 200


@teacher_ai_games_blueprint.route('/api/students/<int:student_id>/adaptive-games', methods=['POST'])
def api_generate_adaptive_game(student_id):
    """Solo el docente puede solicitar una práctica adaptativa desde un material suyo."""
    denied = _teacher_check()
    if denied:
        return denied
    payload = request.get_json() or {}
    material_id = payload.get('material_id')
    if not material_id:
        return jsonify({'success': False, 'error': 'Debes seleccionar un material docente.'}), 400
    result = AdaptiveGameGeneratorService.generate_for_student(
        student_id=student_id,
        material_id=int(material_id),
        game_type=payload.get('game_type', 'multiple_choice'),
        created_by=session.get('user_id'),
    )
    if not result.get('success'):
        return jsonify(result), 422
    return jsonify(result), 201


# =========================================================================
# Generación de Juegos con IA a partir de Materiales / Presentaciones
# =========================================================================

@teacher_ai_games_blueprint.route('/api/materials/<int:material_id>/generate-game', methods=['POST'])
def api_generate_game_from_material(material_id):
    """
    Genera un juego educativo por IA utilizando Ollama a partir del material de texto docente.
    """
    denied = _teacher_check()
    if denied:
        return denied

    material = fetch_material_by_id(material_id)
    if not material:
        return jsonify({'error': 'Material educativo no encontrado', 'success': False}), 404

    payload = request.get_json() or {}
    game_type = payload.get('game_type', 'multiple_choice')
    grade = int(material.get('grade') or session.get('user_grade') or 5)

    # 1. Extracción de contenido
    extracted = MaterialExtractorService.extract_from_text(
        text=material.get('content') or material.get('description') or material.get('title'),
        title=material.get('title', 'Tema Educativo'),
    )

    # 2. Generación por IA con Ollama (y fallback offline garantizado)
    gen_result = AIGameGeneratorService.generate_game(
        material_data=extracted,
        game_type=game_type,
        grade=grade,
    )

    if not gen_result.get('success'):
        return jsonify({
            'error': gen_result.get('error', 'Error generando el juego educativo'),
            'success': False,
        }), 500

    game_obj = gen_result['game']

    # 3. Validación automática antes de guardar
    is_valid, val_err, clean_game = GameValidationService.validate(game_obj)
    if not is_valid or not clean_game:
        return jsonify({
            'error': f'El juego generado no superó la validación pedagógica: {val_err}',
            'success': False,
        }), 422

    # 4. Persistir con ciclo de gobernanza docente en PENDING_REVIEW
    game_id = create_ai_generated_game(
        topic_id=int(material.get('topic_id', 1)),
        material_id=material_id,
        presentation_id=None,
        game_type=clean_game['game_type'],
        title=clean_game['title'],
        instruction=clean_game['instruction'],
        content_json=_content_with_metadata(clean_game),
        status='PENDING_REVIEW',
        created_by=session.get('user_id'),
    )

    saved_game = fetch_ai_generated_game_by_id(game_id)
    return jsonify({
        'success': True,
        'message': 'Juego generado exitosamente y listo para revisión docente.',
        'game_id': game_id,
        'status': 'PENDING_REVIEW',
        'source': gen_result.get('source'),
        'notice': gen_result.get('notice'),
        'game': saved_game,
    }), 201


@teacher_ai_games_blueprint.route('/api/presentations/<int:presentation_id>/generate-game', methods=['POST'])
def api_generate_game_from_presentation(presentation_id):
    """
    Genera un juego educativo por IA utilizando Ollama a partir de una presentación PPT/PPTX del profesor.
    """
    denied = _teacher_check()
    if denied:
        return denied

    presentation = fetch_presentation_by_id(presentation_id)
    if not presentation:
        return jsonify({'error': 'Presentación no encontrada', 'success': False}), 404

    payload = request.get_json() or {}
    game_type = payload.get('game_type', 'multiple_choice')
    grade = int(presentation.get('grade') or session.get('user_grade') or 5)

    # 1. Extracción de contenido PPTX/PPT/Texto
    try:
        extracted = _extract_presentation_content(presentation)
    except (FileNotFoundError, ValueError, OSError) as exc:
        return jsonify({'error': str(exc), 'success': False}), 400

    # 2. Generación por IA con Ollama (y fallback offline garantizado)
    gen_result = AIGameGeneratorService.generate_game(
        material_data=extracted,
        game_type=game_type,
        grade=grade,
    )

    if not gen_result.get('success'):
        return jsonify({
            'error': gen_result.get('error', 'Error generando el juego educativo'),
            'success': False,
        }), 500

    game_obj = gen_result['game']

    # 3. Validación automática
    is_valid, val_err, clean_game = GameValidationService.validate(game_obj)
    if not is_valid or not clean_game:
        return jsonify({
            'error': f'El juego generado no superó la validación pedagógica: {val_err}',
            'success': False,
        }), 422

    # 4. Persistir con ciclo de gobernanza docente en PENDING_REVIEW
    game_id = create_ai_generated_game(
        topic_id=int(presentation.get('topic_id', 1)),
        material_id=None,
        presentation_id=presentation_id,
        game_type=clean_game['game_type'],
        title=clean_game['title'],
        instruction=clean_game['instruction'],
        content_json=_content_with_metadata(clean_game),
        status='PENDING_REVIEW',
        created_by=session.get('user_id'),
    )

    saved_game = fetch_ai_generated_game_by_id(game_id)
    return jsonify({
        'success': True,
        'message': 'Juego generado exitosamente desde la presentación PPT.',
        'game_id': game_id,
        'status': 'PENDING_REVIEW',
        'source': gen_result.get('source'),
        'notice': gen_result.get('notice'),
        'game': saved_game,
    }), 201


# =========================================================================
# Gestión y Ciclo de Aprobación Docente de Juegos IA
# =========================================================================

@teacher_ai_games_blueprint.route('/api/ai-games', methods=['GET'])
def api_list_ai_games():
    """
    Retorna la lista de juegos generados por IA, con filtros opcionales de topic_id o status.
    """
    denied = _teacher_check()
    if denied:
        return denied

    topic_id = request.args.get('topic_id', type=int)
    status = request.args.get('status')
    presentation_id = request.args.get('presentation_id', type=int)
    material_id = request.args.get('material_id', type=int)
    grade = request.args.get('grade', type=int)
    unit_number = request.args.get('unit', type=int)
    session_number = request.args.get('session_number', type=int)
    section = (request.args.get('section') or '').strip() or None
    if unit_number is not None and not 1 <= unit_number <= 8:
        return jsonify({'error': 'Unidad no válida', 'success': False}), 400
    if session_number is not None and not 1 <= session_number <= 32:
        return jsonify({'error': 'Sesión no válida', 'success': False}), 400

    games = fetch_ai_generated_games(
        topic_id=topic_id,
        status=status,
        presentation_id=presentation_id,
        material_id=material_id,
        grade=grade,
        section=section,
        unit_number=unit_number,
        session_number=session_number,
    )
    return jsonify({
        'success': True,
        'games': games,
        'total': len(games),
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>', methods=['GET'])
def api_get_ai_game(game_id):
    """
    Retorna el detalle completo de un juego generado por IA.
    """
    denied = _teacher_check()
    if denied:
        return denied

    game = fetch_ai_generated_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    return jsonify({
        'success': True,
        'game': game,
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>', methods=['PUT'])
def api_update_ai_game(game_id):
    """
    Permite al docente editar título, instrucciones o contenido del juego generado.
    """
    denied = _teacher_check()
    if denied:
        return denied

    existing = fetch_ai_generated_game_by_id(game_id)
    if not existing:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    data = request.get_json() or {}
    new_title = data.get('title', existing.get('title'))
    new_instruction = data.get('instruction', existing.get('instruction'))
    new_content = data.get('content_json', existing.get('content_json'))
    new_status = data.get('status', existing.get('status'))
    if new_status != existing.get('status'):
        return jsonify({
            'error': 'Los cambios de estado deben hacerse mediante aprobar o publicar para conservar la revisión docente.',
            'success': False,
        }), 409

    # Si se editó el contenido, validar estructura
    existing_metadata = (existing.get('content_json') or {}).get('_meta') or {}
    candidate = {
        'game_type': existing.get('game_type'),
        'title': new_title,
        'instruction': new_instruction,
        'content': new_content,
        **existing_metadata,
    }
    if data.get('difficulty'):
        candidate['difficulty'] = data['difficulty']
    is_valid, err_msg, validated = GameValidationService.validate(candidate)
    if not is_valid or not validated:
        return jsonify({'error': f'Los cambios no son válidos: {err_msg}', 'success': False}), 400

    stored_content = dict(existing.get('content_json') or {})
    stored_content.pop('_meta', None)
    changed = (validated['title'] != existing.get('title')
               or validated['instruction'] != existing.get('instruction')
               or validated['content'] != stored_content
               or validated.get('difficulty') != existing_metadata.get('difficulty', 'easy'))
    if changed:
        new_status = 'PENDING_REVIEW'

    update_ai_generated_game(
        game_id=game_id,
        title=validated['title'],
        instruction=validated['instruction'],
        content_json=_content_with_metadata(validated),
        status=new_status,
    )

    updated = fetch_ai_generated_game_by_id(game_id)
    return jsonify({
        'success': True,
        'message': 'Juego actualizado correctamente por el profesor.',
        'game': updated,
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>/regenerate', methods=['POST'])
def api_regenerate_ai_game(game_id):
    """Regenera el mismo juego desde su material original y lo devuelve a revisión."""
    denied = _teacher_check()
    if denied:
        return denied
    existing = fetch_ai_generated_game_by_id(game_id)
    if not existing:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    payload = request.get_json() or {}
    game_type = payload.get('game_type') or existing.get('game_type')
    metadata = (existing.get('content_json') or {}).get('_meta') or {}
    grade = int(payload.get('grade') or metadata.get('grade') or session.get('user_grade') or 5)

    material = fetch_material_by_id(existing.get('material_id')) if existing.get('material_id') else None
    presentation = fetch_presentation_by_id(existing.get('presentation_id')) if existing.get('presentation_id') else None
    if material:
        extracted = MaterialExtractorService.extract_from_text(
            material.get('content') or material.get('description') or material.get('title', ''),
            title=material.get('title', 'Tema Educativo'),
        )
    elif presentation:
        try:
            extracted = _extract_presentation_content(presentation)
        except (FileNotFoundError, ValueError, OSError) as exc:
            return jsonify({'error': str(exc), 'success': False}), 400
    else:
        return jsonify({'error': 'No se encontró el material original para regenerar.', 'success': False}), 409

    generated = AIGameGeneratorService.generate_game(extracted, game_type=game_type, grade=grade)
    is_valid, error, clean_game = GameValidationService.validate(generated.get('game'))
    if not is_valid or not clean_game:
        return jsonify({'error': f'La nueva versión no superó la validación: {error}', 'success': False}), 422
    if payload.get('difficulty'):
        clean_game['difficulty'] = str(payload['difficulty']).lower()
    update_ai_generated_game(
        game_id,
        title=clean_game['title'],
        instruction=clean_game['instruction'],
        content_json=_content_with_metadata(clean_game),
        status='PENDING_REVIEW',
    )
    return jsonify({
        'success': True,
        'message': 'Juego regenerado y enviado nuevamente a revisión.',
        'status': 'PENDING_REVIEW',
        'game': fetch_ai_generated_game_by_id(game_id),
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>/approve', methods=['POST'])
def api_approve_ai_game(game_id):
    """
    Cambia el estado del juego a APPROVED.
    """
    denied = _teacher_check()
    if denied:
        return denied

    game = fetch_ai_generated_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404
    if game.get('status') not in {'GENERATED', 'PENDING_REVIEW'}:
        return jsonify({'error': 'Solo se pueden aprobar juegos pendientes de revisión.', 'success': False}), 409

    update_ai_generated_game_status(game_id, 'APPROVED')
    return jsonify({
        'success': True,
        'message': 'Juego aprobado por el profesor.',
        'status': 'APPROVED',
        'game_id': game_id,
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>/publish', methods=['POST'])
def api_publish_ai_game(game_id):
    """
    Publica el juego (estado PUBLISHED) para que los alumnos puedan verlo y jugarlo.
    """
    denied = _teacher_check()
    if denied:
        return denied

    game = fetch_ai_generated_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404
    if game.get('status') != 'APPROVED':
        return jsonify({'error': 'El juego debe estar aprobado antes de publicarse.', 'success': False}), 409

    update_ai_generated_game_status(game_id, 'PUBLISHED')
    return jsonify({
        'success': True,
        'message': '¡Juego publicado para los alumnos exitosamente!',
        'status': 'PUBLISHED',
        'game_id': game_id,
    }), 200


@teacher_ai_games_blueprint.route('/api/ai-games/<int:game_id>', methods=['DELETE'])
def api_delete_ai_game(game_id):
    """
    Elimina o rechaza un juego generado por IA.
    """
    denied = _teacher_check()
    if denied:
        return denied

    game = fetch_ai_generated_game_by_id(game_id)
    if not game:
        return jsonify({'error': 'Juego no encontrado', 'success': False}), 404

    delete_ai_generated_game(game_id)
    return jsonify({
        'success': True,
        'message': 'Juego eliminado correctamente.',
        'game_id': game_id,
    }), 200
