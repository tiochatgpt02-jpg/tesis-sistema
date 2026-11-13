import re
import json
from typing import Dict, Any, Tuple, Optional, List
from services.game_engine import GameEngine


class GameValidationService:
    """
    Servicio de validación automática para juegos educativos generados por IA.
    Asegura que la estructura cumpla con el esquema requerido para niños de primaria
    antes de ser presentada para revisión docente.
    """

    ALLOWED_GAME_TYPES = set(GameEngine.GAME_TYPES)

    @classmethod
    def validate(cls, raw_data: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Valida y normaliza el juego generado por IA.
        Retorna: (is_valid, error_message, normalized_payload)
        """
        if not raw_data:
            return False, "Los datos del juego están vacíos.", None

        # Si viene como cadena, intentar deserializar
        payload = raw_data
        if isinstance(payload, str):
            try:
                # Quitar markdown si viene envuelto
                cleaned = re.sub(r'^```json\s*', '', payload.strip(), flags=re.IGNORECASE)
                cleaned = re.sub(r'\s*```$', '', cleaned)
                payload = json.loads(cleaned)
            except Exception as e:
                # Búsqueda heurística de llaves JSON
                match = re.search(r'\{[\s\S]*\}', payload)
                if match:
                    try:
                        payload = json.loads(match.group())
                    except Exception:
                        return False, f"Error al parsear el JSON generado: {str(e)}", None
                else:
                    return False, f"Formato JSON inválido: {str(e)}", None

        if not isinstance(payload, dict):
            return False, "La raíz del juego generado debe ser un objeto JSON.", None

        game_type = GameEngine.normalize_type(payload.get('game_type') or payload.get('type'))

        if game_type not in cls.ALLOWED_GAME_TYPES:
            return False, f"Tipo de juego no soportado: '{game_type}'. Permitidos: {list(cls.ALLOWED_GAME_TYPES)}", None

        title = str(payload.get('title') or payload.get('titulo') or '').strip()
        if len(title) < 3:
            return False, "El título del juego es demasiado corto o está vacío.", None

        instruction = str(payload.get('instruction') or payload.get('instruccion') or payload.get('instrucciones') or '').strip()
        if not instruction:
            # Asignar instrucción por defecto según tipo
            if game_type == 'multiple_choice':
                instruction = "Selecciona la opción correcta para ganar puntos."
            elif game_type == 'true_false':
                instruction = "Indica si la afirmación es Verdadera o Falsa."
            elif game_type == 'fill_blank':
                instruction = "Completa el espacio con la palabra correcta."
            elif game_type == 'matching':
                instruction = "Une cada concepto con su significado correspondiente."

        content = payload.get('content') or payload.get('contenido') or payload.get('data') or {}
        if not isinstance(content, dict):
            content = {}

        if cls._contains_html(payload):
            return False, "El juego no puede contener HTML. La IA solo debe entregar datos de la actividad.", None

        # 1. Validación de Multiple Choice
        if game_type == 'multiple_choice':
            question = str(content.get('question') or content.get('pregunta') or payload.get('question') or '').strip()
            if len(question) < 5:
                return False, "La pregunta del juego de opción múltiple es demasiado corta o no fue provista.", None

            options = content.get('options') or content.get('opciones') or payload.get('options') or []
            if not isinstance(options, list) or len(options) < 2:
                return False, "El juego de opción múltiple debe contener al menos 2 opciones de respuesta.", None

            clean_options = [str(opt).strip() for opt in options if str(opt).strip()]
            if len(clean_options) < 2:
                return False, "Las opciones no contienen texto válido.", None

            answer = str(content.get('answer') or content.get('correct_answer') or content.get('respuesta') or payload.get('answer') or '').strip()
            if not answer:
                return False, "No se indicó la respuesta correcta.", None

            # Verificar si la respuesta está entre las opciones (insensible a mayúsculas)
            matched_answer = next((opt for opt in clean_options if opt.lower() == answer.lower()), None)
            if not matched_answer:
                # Si no está explícitamente, añadirla a las opciones si hay espacio
                if len(clean_options) < 4:
                    clean_options.append(answer)
                    matched_answer = answer
                else:
                    return False, f"La respuesta '{answer}' no coincide con ninguna de las opciones provistas.", None

            explanation = str(content.get('explanation') or content.get('explicacion') or f"¡Muy bien! '{matched_answer}' es la respuesta correcta.").strip()

            normalized_content = {
                'question': question,
                'options': clean_options[:4],
                'answer': matched_answer,
                'explanation': explanation,
            }

        # 2. Validación de Verdadero / Falso
        elif game_type == 'true_false':
            statement = str(content.get('statement') or content.get('afirmacion') or content.get('pregunta') or content.get('question') or payload.get('statement') or '').strip()
            if len(statement) < 5:
                return False, "La afirmación del juego Verdadero/Falso es demasiado corta o vacía.", None

            raw_answer = content.get('correct_answer') if 'correct_answer' in content else content.get('answer', content.get('respuesta'))
            if raw_answer is None and 'correct_answer' in payload:
                raw_answer = payload.get('correct_answer')

            if isinstance(raw_answer, bool):
                correct_bool = raw_answer
            elif str(raw_answer).lower().strip() in ('true', 'verdadero', 'v', 'cierto', '1', 'si', 'sí'):
                correct_bool = True
            elif str(raw_answer).lower().strip() in ('false', 'falso', 'f', '0', 'no'):
                correct_bool = False
            else:
                return False, "La respuesta de Verdadero/Falso debe ser un valor booleano o 'Verdadero'/'Falso'.", None

            explanation = str(content.get('explanation') or content.get('explicacion') or (
                "¡Correcto! La afirmación es Verdadera." if correct_bool else "¡Correcto! La afirmación es Falsa."
            )).strip()

            normalized_content = {
                'statement': statement,
                'correct_answer': correct_bool,
                'explanation': explanation,
            }

        # 3. Validación de Completar Espacios (Fill in the blank)
        elif game_type == 'fill_blank':
            sentence = str(content.get('sentence') or content.get('oracion') or content.get('pregunta') or payload.get('sentence') or '').strip()
            blank_word = str(content.get('blank_word') or content.get('palabra') or content.get('answer') or content.get('correct_answer') or '').strip()
            answers = content.get('answers') or content.get('respuestas') or ([blank_word] if blank_word else [])
            options = content.get('options') or content.get('opciones') or []

            if len(sentence) < 5:
                return False, "La oración a completar es demasiado corta o no fue provista.", None

            # Si la oración no tiene guiones bajos o placeholder, asegurar que contenga el blank_word
            if '___' not in sentence and blank_word:
                if re.search(re.escape(blank_word), sentence, flags=re.IGNORECASE):
                    sentence = re.sub(re.escape(blank_word), '______', sentence, count=1, flags=re.IGNORECASE)
                else:
                    sentence += ' ______'
            elif '___' not in sentence and not blank_word:
                return False, "La oración no contiene un espacio para completar ('______').", None

            if not answers and blank_word:
                answers = [blank_word]

            if not answers or not str(answers[0]).strip():
                return False, "No se indicó la palabra o respuesta correcta para completar.", None

            target_word = str(answers[0]).strip()
            clean_options = [str(opt).strip() for opt in options if str(opt).strip()]
            if target_word not in clean_options:
                clean_options.append(target_word)

            if len(clean_options) < 2:
                # Distractores genéricos si faltan
                clean_options.extend(["Ninguno", "Otro"])

            explanation = str(content.get('explanation') or content.get('explicacion') or f"La palabra correcta es '{target_word}'.").strip()

            normalized_content = {
                'sentence': sentence,
                'blank_word': target_word,
                'answers': [target_word],
                'options': clean_options[:4],
                'explanation': explanation,
            }

        # 4. Validación de Matching (Unir conceptos)
        elif game_type == 'matching':
            pairs = content.get('pairs') or content.get('pares') or content.get('parejas') or payload.get('pairs') or []
            if not isinstance(pairs, list) or len(pairs) < 2:
                return False, "El juego de unir conceptos debe contener al menos 2 parejas.", None

            clean_pairs = []
            for p in pairs:
                if not isinstance(p, dict):
                    continue
                left = str(p.get('left') or p.get('termino') or p.get('concepto') or '').strip()
                right = str(p.get('right') or p.get('definicion') or p.get('significado') or '').strip()
                if left and right:
                    clean_pairs.append({'left': left, 'right': right})

            if len(clean_pairs) < 2:
                return False, "Se requieren al menos 2 parejas válidas con término y definición.", None

            explanation = str(content.get('explanation') or content.get('explicacion') or "¡Excelente trabajo relacionando todos los conceptos!").strip()

            normalized_content = {
                'pairs': clean_pairs[:6],
                'explanation': explanation,
            }

        # 5. Memory Cards: cada pareja se renderiza en dos cartas por el frontend.
        elif game_type == 'memory':
            pairs = content.get('pairs') or content.get('cards') or []
            clean_pairs = cls._clean_pairs(pairs)
            if len(clean_pairs) < 2:
                return False, "El juego de memoria requiere al menos 2 parejas de cartas.", None
            normalized_content = {
                'pairs': clean_pairs[:6],
                'explanation': str(content.get('explanation') or content.get('explicacion') or "¡Encontraste una pareja! Sigue buscando.").strip(),
            }

        # 6. Ordering: el orden almacenado es la solución, nunca la presentación visual.
        elif game_type == 'ordering':
            items = cls._clean_strings(content.get('items') or content.get('steps') or content.get('sequence') or [])
            if len(items) < 3:
                return False, "El juego de ordenar requiere al menos 3 pasos o conceptos.", None
            normalized_content = {
                'items': items[:8],
                'explanation': str(content.get('explanation') or content.get('explicacion') or "¡Ordenaste la secuencia correctamente!").strip(),
            }

        # 7. Drag & Drop: elementos a clasificar y categorías explícitas.
        elif game_type == 'drag_drop':
            raw_items = content.get('items') or content.get('draggables') or []
            clean_items = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                label = str(item.get('item') or item.get('label') or item.get('text') or '').strip()
                category = str(item.get('category') or item.get('target') or '').strip()
                if label and category:
                    clean_items.append({'item': label, 'category': category})
            categories = cls._clean_strings(content.get('categories') or [item['category'] for item in clean_items])
            if len(clean_items) < 2 or len(categories) < 2:
                return False, "Arrastrar y soltar requiere 2 o más elementos y 2 o más categorías.", None
            normalized_content = {
                'items': clean_items[:10],
                'categories': categories[:6],
                'explanation': str(content.get('explanation') or content.get('explicacion') or "¡Clasificaste los elementos como un experto!").strip(),
            }

        # 8. Challenge: aventura de 3 niveles con una pregunta de opción múltiple por nivel.
        elif game_type == 'challenge':
            raw_levels = content.get('levels') or []
            levels = []
            for index, level in enumerate(raw_levels[:3], start=1):
                if not isinstance(level, dict):
                    continue
                question = str(level.get('question') or '').strip()
                options = cls._clean_strings(level.get('options') or [])
                answer = str(level.get('answer') or level.get('correct_answer') or '').strip()
                if len(question) >= 5 and len(options) >= 2 and answer:
                    if not any(option.lower() == answer.lower() for option in options):
                        options.append(answer)
                    levels.append({'level': int(level.get('level') or index), 'question': question, 'options': options[:4], 'answer': answer})
            if len(levels) < 3:
                return False, "La aventura por niveles requiere exactamente 3 retos válidos.", None
            normalized_content = {
                'levels': levels,
                'explanation': str(content.get('explanation') or content.get('explicacion') or "¡Superaste toda la aventura!").strip(),
            }

        # Validar longitud adecuada para niños de primaria (frases no gigantescas)
        total_text_len = len(title) + len(instruction) + len(str(normalized_content))
        if total_text_len > 4000:
            return False, "El contenido generado es demasiado extenso para una actividad de primaria.", None

        normalized_game = {
            'game_type': game_type,
            'title': title,
            'instruction': instruction,
            'content': normalized_content,
            'description': str(payload.get('description') or '').strip(),
            'subject': str(payload.get('subject') or '').strip(),
            'grade': str(payload.get('grade') or '').strip(),
            'difficulty': str(payload.get('difficulty') or 'easy').lower().strip(),
            'learning_objective': str(payload.get('learning_objective') or '').strip(),
            'content_reference': str(payload.get('content_reference') or '').strip(),
            'feedback_correct': str(payload.get('feedback_correct') or '').strip(),
            'feedback_wrong': str(payload.get('feedback_wrong') or '').strip(),
        }

        return True, "", normalized_game

    @staticmethod
    def _clean_strings(values: Any) -> List[str]:
        if not isinstance(values, list):
            return []
        unique = []
        seen = set()
        for value in values:
            item = str(value).strip()
            if item and item.lower() not in seen:
                seen.add(item.lower())
                unique.append(item)
        return unique

    @classmethod
    def _clean_pairs(cls, values: Any) -> List[Dict[str, str]]:
        if not isinstance(values, list):
            return []
        pairs = []
        for value in values:
            if not isinstance(value, dict):
                continue
            left = str(value.get('left') or value.get('term') or value.get('concept') or '').strip()
            right = str(value.get('right') or value.get('definition') or value.get('meaning') or '').strip()
            if left and right:
                pairs.append({'left': left, 'right': right})
        return pairs

    @classmethod
    def _contains_html(cls, value: Any) -> bool:
        if isinstance(value, str):
            return bool(re.search(r'</?[a-z][^>]*>', value, flags=re.IGNORECASE))
        if isinstance(value, dict):
            return any(cls._contains_html(item) for item in value.values())
        if isinstance(value, list):
            return any(cls._contains_html(item) for item in value)
        return False
