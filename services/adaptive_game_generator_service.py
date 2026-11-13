"""Generación de práctica adaptativa bajo control explícito del docente."""
from typing import Any, Dict

from services import db_service
from services.adaptive_learning_service import build_adaptive_learning_profile
from services.ai_game_generator_service import AIGameGeneratorService
from services.game_validation_service import GameValidationService
from services.material_extractor_service import MaterialExtractorService


class AdaptiveGameGeneratorService:
    @staticmethod
    def _content_with_metadata(game: Dict[str, Any], adaptive: Dict[str, Any]) -> Dict[str, Any]:
        content = dict(game.get('content') or {})
        content['_meta'] = {key: game.get(key, '') for key in ('description', 'subject', 'grade', 'difficulty', 'learning_objective', 'content_reference', 'feedback_correct', 'feedback_wrong')}
        content['_meta']['adaptive_learning'] = {'weak_topic': adaptive['weak_topic'], 'recommended_difficulty': adaptive['difficulty'], 'source': 'student_performance_analysis'}
        return content

    @classmethod
    def generate_for_student(cls, student_id: int, material_id: int, game_type: str = 'multiple_choice', created_by: int | None = None) -> Dict[str, Any]:
        """Genera y guarda un juego en PENDING_REVIEW; nunca lo publica."""
        profile = build_adaptive_learning_profile(student_id)
        weak_topics = profile.get('weak_topics') or []
        if not weak_topics:
            return {'success': False, 'error': 'No hay evidencia suficiente para elegir un tema de refuerzo.', 'profile': profile}
        weak_topic = weak_topics[0]
        material = db_service.fetch_material_by_id(material_id)
        if not material:
            return {'success': False, 'error': 'Material docente no encontrado.', 'profile': profile}
        if int(material.get('topic_id') or 0) != int(weak_topic.get('topic_id') or 0):
            return {'success': False, 'error': 'El material elegido no corresponde al tema débil detectado.', 'profile': profile}
        student = db_service.fetch_student_by_id(student_id) or {}
        extracted = MaterialExtractorService.extract_from_text(material.get('content') or material.get('description') or material.get('title', ''), title=material.get('title') or weak_topic['title'])
        context = {'weak_topic': weak_topic['title'], 'difficulty': profile['recommended_difficulty'], 'instruction': 'Ajusta la complejidad al nivel indicado sin añadir datos fuera del material docente.'}
        generated = AIGameGeneratorService.generate_game(material_data=extracted, game_type=game_type, grade=int(student.get('grade') or material.get('grade') or 5), adaptation_context=context)
        valid, error, game = GameValidationService.validate(generated.get('game'))
        if not valid or not game:
            return {'success': False, 'error': f'El juego adaptativo no superó la validación: {error}', 'profile': profile}
        game['difficulty'] = profile['recommended_difficulty']
        game_id = db_service.create_ai_generated_game(topic_id=int(weak_topic['topic_id']), material_id=int(material_id), presentation_id=None, game_type=game['game_type'], title=game['title'], instruction=game['instruction'], content_json=cls._content_with_metadata(game, {'weak_topic': weak_topic['title'], 'difficulty': profile['recommended_difficulty']}), status='PENDING_REVIEW', created_by=created_by)
        return {'success': True, 'game_id': game_id, 'status': 'PENDING_REVIEW', 'generation_status': 'GENERATED', 'source': generated.get('source'), 'profile': profile, 'game': db_service.fetch_ai_generated_game_by_id(game_id)}
