import os
import re
import json
import random
from typing import Dict, Any, Optional

from config import Config
from services.game_validation_service import GameValidationService
from services.game_engine import GameEngine


class AIGameGeneratorService:
    """
    Servicio generador de juegos educativos usando el proveedor de IA configurado.
    basado estrictamente en material del docente, con validador integrado
    y generador heurístico de respaldo offline.
    """

    @classmethod
    def _call_ollama(cls, prompt: str, timeout: int = 120) -> str:
        """
        Conserva el nombre de compatibilidad y delega al proveedor por API.
        """
        from services.llm_service import generate_text
        return generate_text(prompt, timeout=timeout, json_mode=True)

    @classmethod
    def generate_game(
        cls,
        material_data: Dict[str, Any],
        game_type: str = 'multiple_choice',
        grade: int = 5,
        adaptation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para la generación del juego educativo.
        Si la API responde y la salida es válida, retorna el juego generado con IA.
        Si falla o está apagado, activa el fallback offline determinista sin romper el sistema.
        """
        title = (material_data.get('title') or 'Tema Educativo').strip()
        raw_text = (material_data.get('raw_text') or '').strip()
        key_points = material_data.get('key_points') or []

        # Si el texto es mínimo, concatenar puntos clave
        context_text = raw_text
        if len(context_text) < 50 and key_points:
            context_text = f"Tema: {title}\n" + "\n".join(f"- {p}" for p in key_points)

        # Si el tipo es 'auto', seleccionar aleatoriamente o ciclar
        target_type = (game_type or 'multiple_choice').lower().strip()
        target_type = GameEngine.normalize_type(game_type)
        if target_type not in GameEngine.GAME_TYPES:
            target_type = 'multiple_choice'

        # Intentar con el proveedor si hay texto. El origen siempre queda visible en
        # desarrollo: un fallback no debe parecer una respuesta del modelo.
        failure_reason = ''
        if context_text:
            prompt = cls._build_pedagogical_prompt(title, context_text, target_type, grade, adaptation_context)
            print(f'[AI] modelo: {Config.AI_PROVIDER}', flush=True)
            print(f'[AI] material: {title}', flush=True)
            print(f'[AI] game_type: {target_type}', flush=True)
            try:
                raw_response = cls._call_ollama(prompt, timeout=Config.AI_TIMEOUT_SECONDS)
                is_valid, err_msg, validated_game = GameValidationService.validate(raw_response)
                grounding_error = cls._grounding_error(validated_game, context_text, target_type) if validated_game else ''
                if is_valid and validated_game and not grounding_error:
                    print(f'[AI] source: {Config.AI_PROVIDER}', flush=True)
                    validated_game = cls._add_game_metadata(validated_game, material_data, grade)
                    return {
                        'success': True,
                        'source': Config.AI_PROVIDER,
                        'notice': f'Juego generado con {Config.AI_PROVIDER}. Revisa el contenido antes de publicarlo.',
                        'game': validated_game,
                    }
                failure_reason = grounding_error or err_msg or 'La respuesta no superó la validación del juego.'
            except Exception as exc:
                failure_reason = str(exc) or exc.__class__.__name__

        # Generador heurístico offline de respaldo
        failure_reason = failure_reason or 'No había texto suficiente del material para consultar la API.'
        print('[AI] El proveedor no pudo generar el contenido.', flush=True)
        print('[AI] source: fallback', flush=True)
        print(f'[AI] reason: {failure_reason}', flush=True)
        fallback_game = cls._offline_fallback_generator(title, context_text, key_points, target_type, grade)
        is_valid, _, clean_game = GameValidationService.validate(fallback_game)
        if not is_valid or not clean_game:
            clean_game = fallback_game
        clean_game = cls._add_game_metadata(clean_game, material_data, grade)

        return {
            'success': True,
            'source': 'fallback',
            'notice': f'Fallback determinista aplicado: {failure_reason}',
            'fallback_reason': failure_reason,
            'game': clean_game,
        }

    @classmethod
    def _build_pedagogical_prompt(cls, title: str, context_text: str, game_type: str, grade: int, adaptation_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Construye el prompt estructurado para niños de primaria según el tipo de juego solicitado.
        """
        example_json = ""
        type_instructions = ""
        adaptation_instruction = ""
        source_facts = [
            line.strip().lstrip('#').lstrip('-').strip()
            for line in context_text.splitlines()
            if len(line.strip().lstrip('#').lstrip('-').strip()) >= 18
            and not line.strip().upper().startswith('ETAPA')
            and 'material de práctica' not in line.lower()
        ]
        if not source_facts:
            source_facts = [
                item.strip() for item in re.split(r'[.;]\s*', context_text)
                if len(item.strip()) >= 18
            ]
        anchor_fact = next(
            (item for item in source_facts if 'cambia' in item.lower() or 'se llama' in item.lower()),
            source_facts[0] if source_facts else title,
        )
        if adaptation_context:
            adaptation_instruction = (
                "AJUSTE ADAPTATIVO (no es contenido factual):\\n"
                f"- Tema a reforzar: {adaptation_context.get('weak_topic', title)}\\n"
                f"- Dificultad requerida: {adaptation_context.get('difficulty', 'medium')}\\n"
                f"- {adaptation_context.get('instruction', 'No agregues hechos fuera del material docente.')}\\n"
            )

        if game_type == 'multiple_choice':
            type_instructions = """
Crea un juego de OPCIÓN MÚLTIPLE para niños de primaria.
Formula 1 pregunta clara y directa basada en el texto del profesor.
Genera 3 o 4 opciones de respuesta cortas donde solo UNA sea la correcta.
La respuesta correcta debe corresponder textualmente a una de las opciones.
La respuesta correcta debe copiar una frase o expresión exacta del PPT; no la parafrasees ni agregues datos.
No uses los textos "Opción correcta", "Distractor", "Concepto 1" ni marcadores genéricos.
"""
            example_json = f"""{{
  "game_type": "multiple_choice",
  "title": "Aventura de {title}",
  "instruction": "Selecciona la respuesta correcta para ganar puntos",
  "content": {{
    "question": "¿Qué dice la presentación sobre este tema?",
    "options": ["{anchor_fact}", "El agua se queda siempre en el mismo lugar", "El Sol enfría el agua de los mares"],
    "answer": "{anchor_fact}",
    "explanation": "La respuesta correcta aparece en la presentación."
  }}
}}"""

        elif game_type == 'true_false':
            type_instructions = """
Crea un juego de VERDADERO O FALSO para niños de primaria.
Genera 1 afirmación interesante y comprensible basada en el texto del profesor.
Indica claramente si la afirmación es verdadera (true) o falsa (false).
"""
            example_json = f"""{{
  "game_type": "true_false",
  "title": "Reto: ¿Verdadero o Falso? - {title}",
  "instruction": "Lee con atención y decide si la afirmación es verdadera o falsa",
  "content": {{
    "statement": "Afirmación clara sobre {title}.",
    "correct_answer": true,
    "explanation": "Explicación educativa que aclara por qué es verdadero o falso."
  }}
}}"""

        elif game_type == 'fill_blank':
            type_instructions = """
Crea un juego de COMPLETAR ESPACIOS para niños de primaria.
Escribe 1 oración donde falte una palabra clave y coloca '______' en su lugar.
Incluye la palabra correcta ('blank_word') y 3 alternativas sencillas ('options').
"""
            example_json = f"""{{
  "game_type": "fill_blank",
  "title": "Completa la palabra mágica de {title}",
  "instruction": "Elige la palabra que completa correctamente la oración",
  "content": {{
    "sentence": "En {title}, el proceso principal ocurre en ______ según lo aprendido.",
    "blank_word": "las hojas",
    "options": ["las hojas", "las piedras", "los cables"],
    "answers": ["las hojas"],
    "explanation": "¡Correcto! Esa palabra completa perfectamente la idea."
  }}
}}"""

        elif game_type == 'matching':
            type_instructions = """
Crea un juego de UNIR CONCEPTOS (Matching) para niños de primaria.
Extrae entre 2 y 4 conceptos clave con su definición o función corta (máximo 6 palabras cada lado).
"""
            example_json = f"""{{
  "game_type": "matching",
  "title": "Conecta los conceptos de {title}",
  "instruction": "Une cada concepto con su significado correspondiente",
  "content": {{
    "pairs": [
      {{"left": "Concepto 1", "right": "Significado 1"}},
      {{"left": "Concepto 2", "right": "Significado 2"}},
      {{"left": "Concepto 3", "right": "Significado 3"}}
    ],
    "explanation": "¡Excelente relación de conceptos!"
  }}
}}"""

        elif game_type == 'memory':
            type_instructions = """
Crea un juego de CARTAS DE MEMORIA para niños de primaria.
Entrega entre 3 y 5 parejas. Cada pareja debe conectar un concepto con una definición, característica o ejemplo corto del material.
"""
            example_json = f"""{{
  "game_type": "memory",
  "title": "Memoria mágica: {title}",
  "instruction": "Encuentra las parejas que van juntas.",
  "content": {{
    "pairs": [{{"left": "Concepto", "right": "Significado corto"}}, {{"left": "Concepto 2", "right": "Significado corto 2"}}],
    "explanation": "Cada pareja te ayuda a recordar una idea importante."
  }}
}}"""

        elif game_type == 'ordering':
            type_instructions = """
Crea un juego de ORDENAR CONCEPTOS para niños de primaria.
Entrega entre 3 y 6 pasos que deban ordenarse, basados solo en un proceso, ciclo, historia o secuencia explícita del material.
"""
            example_json = f"""{{
  "game_type": "ordering",
  "title": "Ordena la aventura: {title}",
  "instruction": "Arrastra los pasos hasta colocarlos en el orden correcto.",
  "content": {{
    "items": ["Primer paso", "Segundo paso", "Tercer paso"],
    "explanation": "El orden te muestra cómo ocurre el proceso."
  }}
}}"""

        elif game_type == 'drag_drop':
            type_instructions = """
Crea un juego de ARRASTRAR Y SOLTAR para niños de primaria.
Define 2 o 3 categorías que aparezcan en el material y al menos 4 elementos para clasificarlas. Cada elemento debe indicar su categoría correcta.
"""
            example_json = f"""{{
  "game_type": "drag_drop",
  "title": "Clasifica y descubre: {title}",
  "instruction": "Arrastra cada elemento a su grupo correcto.",
  "content": {{
    "categories": ["Categoría A", "Categoría B"],
    "items": [{{"item": "Elemento 1", "category": "Categoría A"}}, {{"item": "Elemento 2", "category": "Categoría B"}}],
    "explanation": "Clasificar te ayuda a comparar las características."
  }}
}}"""

        elif game_type == 'challenge':
            type_instructions = """
Crea una AVENTURA POR NIVELES con exactamente 3 preguntas de opción múltiple. El nivel 1 debe ser sencillo, el 2 relacionar conceptos y el 3 aplicar una idea del material. Cada nivel debe tener 2 a 4 opciones y una respuesta correcta.
"""
            example_json = f"""{{
  "game_type": "challenge",
  "title": "Aventura de {title}",
  "instruction": "Supera los tres niveles de la misión.",
  "content": {{
    "levels": [
      {{"level": 1, "question": "Pregunta sencilla", "options": ["Correcta", "Otra"], "answer": "Correcta"}},
      {{"level": 2, "question": "Pregunta para relacionar", "options": ["Correcta", "Otra"], "answer": "Correcta"}},
      {{"level": 3, "question": "Pregunta para aplicar", "options": ["Correcta", "Otra"], "answer": "Correcta"}}
    ],
    "explanation": "¡Terminaste los tres niveles de la misión!"
  }}
}}"""

        prompt = f"""Eres un diseñador de actividades y juegos educativos para niños de educación primaria ({grade}° de primaria).
Tu objetivo es transformar el material del profesor en una actividad divertida, clara y motivadora.

MATERIAL EDUCATIVO DEL PROFESOR:
\"\"\"
Título: {title}
{context_text[:2500]}
\"\"\"

INSTRUCCIONES PEDAGÓGICAS:
1. Utiliza ÚNICAMENTE la información provista en el material del profesor. CERO alucinaciones.
2. Emplea lenguaje sencillo, positivo y adecuado para niños de {grade}° de primaria.
3. {type_instructions.strip()}
{adaptation_instruction}4. No generes HTML, CSS, JavaScript ni etiquetas: solo datos JSON.
5. Devuelve ÚNICAMENTE la estructura en JSON válido, sin texto introductorio ni bloques markdown fuera del JSON.

ESTRUCTURA JSON EXACTA:
{example_json}
"""
        return prompt

    @staticmethod
    def _add_game_metadata(game: Dict[str, Any], material_data: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Completa el contrato común con evidencia proveniente del material, no del modelo."""
        enriched = dict(game)
        summary = material_data.get('learning_summary') or {}
        concepts = summary.get('concepts') or material_data.get('key_points') or []
        title = material_data.get('title') or enriched.get('title') or 'Tema Educativo'
        if not enriched.get('description'):
            enriched['description'] = f'Actividad interactiva sobre {title}.'
        if not enriched.get('subject'):
            enriched['subject'] = str(summary.get('topic') or title)
        if not enriched.get('grade'):
            enriched['grade'] = str(grade)
        if not enriched.get('difficulty'):
            enriched['difficulty'] = 'easy'
        if not enriched.get('learning_objective'):
            content = enriched.get('content') or {}
            pairs = content.get('pairs') or []
            primary_concept = next(
                (str(pair.get('left')).strip() for pair in pairs if isinstance(pair, dict) and str(pair.get('left') or '').strip()),
                '',
            )
            enriched['learning_objective'] = primary_concept or (concepts[0] if concepts else f'Practicar ideas del tema {title}.')
        if not enriched.get('content_reference'):
            enriched['content_reference'] = f'Material docente: {title}'
        if not enriched.get('feedback_correct'):
            enriched['feedback_correct'] = '¡Excelente! Aprendiste una idea importante de la clase.'
        if not enriched.get('feedback_wrong'):
            enriched['feedback_wrong'] = '¡Casi! Revisa una pista del material y vuelve a intentarlo.'
        return enriched

    @classmethod
    def _offline_fallback_generator(
        cls,
        title: str,
        context_text: str,
        key_points: list,
        game_type: str,
        grade: int,
    ) -> Dict[str, Any]:
        """
        Generador heurístico determinista de respaldo cuando Ollama no está disponible.
        Garantiza que siempre se genere un juego funcional fundamentado en el texto del docente.
        """
        safe_title = (title or 'Tema Educativo').strip()
        cleaned_text = ' '.join((context_text or '').split())
        content_facts = []
        for raw_line in str(context_text or '').splitlines():
            raw_line = raw_line.strip()
            if not raw_line.startswith(('-', '*')):
                continue
            fact = re.sub(r'^[-*]\s*', '', raw_line).strip()
            if (
                len(fact) >= 15
                and not fact.upper().startswith('ETAPA')
                and not fact.lower().startswith(('material de ', 'ciencias naturales'))
            ):
                content_facts.append(fact)
        sentences = content_facts or [s.strip() for s in re.split(r'[.;]\s*', cleaned_text) if len(s.strip()) >= 15]

        # 1. Multiple Choice Fallback
        if game_type == 'multiple_choice':
            # The four supplied primary presentations are concise definition and
            # list lessons. Reuse the source-locked practice question when it
            # applies so that a fallback is still a child-friendly game, not a
            # generic sentence-selection exercise.
            try:
                from services.ai_service import _primary_ppt_questions
                structured_questions = _primary_ppt_questions(context_text, safe_title)
            except ImportError:
                structured_questions = []
            if structured_questions:
                question = structured_questions[0]
                return {
                    'game_type': 'multiple_choice',
                    'title': f"Reto Mágico: {safe_title}",
                    'instruction': 'Lee la pregunta y elige la respuesta correcta.',
                    'content': {
                        'question': question['question'],
                        'options': question['options'],
                        'answer': question['answer'],
                        'explanation': f"La presentación indica: {question['reference_fragment']}.",
                    },
                }

            # Prefer explicit ``concept; definition`` or ``concept: definition``
            # lines.  They produce a real question and factual distractors from
            # the same PPT (rather than generic filler choices).
            labeled_facts = []
            for fact in sentences:
                match = re.match(r'^([^;:]{3,55})\s*[;:]\s*(.{12,})$', fact)
                if not match:
                    continue
                label, definition = (part.strip() for part in match.groups())
                if label.lower().startswith(('tema', 'prof', 'computación')):
                    continue
                if label and definition:
                    labeled_facts.append((label, definition.rstrip('.')))

            if len(labeled_facts) >= 2:
                answer_frag, definition = labeled_facts[0]
                option_candidates = [label for label, _ in labeled_facts]
                for fact in sentences:
                    compact = fact.strip().rstrip('.;:')
                    words = compact.split()
                    if (
                        1 <= len(words) <= 8
                        and ':' not in compact
                        and ';' not in compact
                        and not compact.lower().startswith(('sus elementos', 'tema', 'prof', 'computación'))
                    ):
                        option_candidates.append(compact)

                options = []
                for label in option_candidates:
                    if label.lower() not in {option.lower() for option in options}:
                        options.append(label)
                    if len(options) == 4:
                        break
                question = (
                    f"Según el material de '{safe_title}', ¿qué elemento se describe así: "
                    f"{definition}?"
                )
                return {
                    'game_type': 'multiple_choice',
                    'title': f"Reto Mágico: {safe_title}",
                    'instruction': "Lee la descripción y selecciona la respuesta correcta.",
                    'content': {
                        'question': question,
                        'options': options,
                        'answer': answer_frag,
                        'explanation': f"El PPT indica: {answer_frag}; {definition}.",
                    },
                }

            if sentences:
                base_sentence = sentences[0]
                answer_frag = base_sentence[:45].rstrip('.').capitalize()
                question = f"Según el material de '{safe_title}', ¿cuál de las siguientes ideas es correcta?"
            else:
                answer_frag = f"Aprender los conceptos fundamentales de {safe_title}"
                question = f"¿Cuál es el objetivo principal del tema '{safe_title}'?"

            options = [
                answer_frag,
                f"Información no relacionada con {safe_title}",
                "Un concepto contrario al material del profesor",
                "Datos externos no explicados en clase",
            ]
            # Mezclar ligeramente manteniendo consistencia
            return {
                'game_type': 'multiple_choice',
                'title': f"Reto Mágico: {safe_title}",
                'instruction': "Selecciona la respuesta correcta basada en la clase.",
                'content': {
                    'question': question,
                    'options': options,
                    'answer': answer_frag,
                    'explanation': f"¡Excelente! El material destaca: '{answer_frag}'.",
                },
            }

        # 2. True / False Fallback
        elif game_type == 'true_false':
            if sentences:
                statement = sentences[0].capitalize()
                if not statement.endswith('.'):
                    statement += '.'
            elif key_points:
                statement = f"{key_points[0].capitalize()} es un concepto clave de {safe_title}."
            else:
                statement = f"El estudio de {safe_title} permite comprender mejor los temas de la clase."

            return {
                'game_type': 'true_false',
                'title': f"¿Verdadero o Falso?: {safe_title}",
                'instruction': "Determina si la afirmación es Verdadera o Falsa según el material.",
                'content': {
                    'statement': statement,
                    'correct_answer': True,
                    'explanation': f"¡Correcto! Es una afirmación verdadera según lo enseñado en {safe_title}.",
                },
            }

        # 3. Fill in the blank Fallback
        elif game_type == 'fill_blank':
            target_word = safe_title.split()[0] if safe_title.split() else "tema"
            source_point = sentences[0] if sentences else (key_points[0] if key_points else '')
            if source_point:
                words = [
                    w for w in re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', source_point)
                    if w.lower() not in ('para', 'como', 'este', 'esta', 'todo', 'material')
                ]
                if words:
                    target_word = words[0]
                    sentence = re.sub(re.escape(target_word), '______', source_point, count=1, flags=re.IGNORECASE)
                else:
                    sentence = f"En la clase de {safe_title}, aprendemos sobre ______."
            else:
                sentence = f"En la clase de {safe_title}, aprendemos sobre ______."

            if '______' not in sentence:
                sentence = f"{sentence} ______"

            distractors = []
            for candidate in re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', ' '.join(sentences[1:])):
                if candidate.lower() != target_word.lower() and candidate not in distractors:
                    distractors.append(candidate)
                if len(distractors) == 2:
                    break
            options = [target_word] + distractors
            while len(options) < 3:
                options.append('otra palabra')
            return {
                'game_type': 'fill_blank',
                'title': f"Completa la Frase: {safe_title}",
                'instruction': "Elige la palabra que completa la oración correctamente.",
                'content': {
                    'sentence': sentence,
                    'blank_word': target_word,
                    'answers': [target_word],
                    'options': options,
                    'explanation': f"¡Muy bien! La palabra faltante es '{target_word}'.",
                },
            }

        # 4. Matching Fallback
        elif game_type == 'matching':
            pairs = cls._section_pairs(context_text, safe_title) or cls._fallback_pairs(
                safe_title, key_points, context_text,
            )

            return {
                'game_type': 'matching',
                'title': f"Conecta y Gana: {safe_title}",
                'instruction': "Une cada concepto con su significado correspondiente.",
                'content': {
                    'pairs': pairs,
                    'explanation': "¡Excelente trabajo! Has conectado correctamente todos los conceptos del tema.",
                },
            }

        base_pairs = cls._section_pairs(context_text, safe_title) or cls._fallback_pairs(
            safe_title, key_points, context_text,
        )
        if game_type == 'memory':
            return {
                'game_type': 'memory',
                'title': f'Memoria Mágica: {safe_title}',
                'instruction': 'Encuentra las parejas que pertenecen juntas.',
                'content': {'pairs': base_pairs, 'explanation': '¡Cada pareja encontrada refuerza lo aprendido!'},
            }

        if game_type == 'ordering':
            # Section headings preserve the order explicitly established by the
            # source presentation, unlike decorative labels such as "ETAPA 1".
            steps = [pair['left'] for pair in base_pairs if str(pair.get('left') or '').strip()]
            if len(steps) < 3:
                steps = [point[:80] for point in sentences[:5] if point.strip()]
            if len(steps) < 3:
                steps = [point[:80] for point in key_points[:5] if point.strip()]
            if len(steps) < 3:
                steps = [safe_title, 'Revisar el material docente', 'Explicar una idea del material']
            return {
                'game_type': 'ordering',
                'title': f'Ordena la Aventura: {safe_title}',
                'instruction': 'Coloca cada paso en el orden en que aparece en la clase.',
                'content': {'items': steps, 'explanation': '¡Ordenar los pasos te ayuda a comprender el proceso!'},
            }

        if game_type == 'drag_drop':
            categories = ['Ideas del tema', 'Ejemplos de la clase']
            items = []
            source = sentences[:6] or key_points[:6] or [safe_title, 'Concepto importante', 'Ejemplo de clase', 'Idea principal']
            for index, point in enumerate(source):
                items.append({'item': point[:70], 'category': categories[index % 2]})
            return {
                'game_type': 'drag_drop',
                'title': f'Clasifica y Descubre: {safe_title}',
                'instruction': 'Arrastra cada tarjeta al grupo que le corresponde.',
                'content': {'categories': categories, 'items': items, 'explanation': '¡Muy bien! Clasificaste las ideas del material.'},
            }

        if game_type == 'challenge':
            fact = (sentences[0] if sentences else (key_points[0] if key_points else f'Aprendemos sobre {safe_title}')).rstrip('.')
            levels = []
            for level in range(1, 4):
                answer = fact[:70]
                levels.append({
                    'level': level,
                    'question': f'Nivel {level}: ¿Cuál idea aparece en el material de {safe_title}?',
                    'options': [answer, 'Una idea ajena a la clase'],
                    'answer': answer,
                })
            return {
                'game_type': 'challenge',
                'title': f'Aventura por Niveles: {safe_title}',
                'instruction': 'Completa los tres niveles para terminar la misión.',
                'content': {'levels': levels, 'explanation': '¡Terminaste toda la aventura!'},
            }

        raise ValueError(f'Tipo de juego no soportado: {game_type}')

    @staticmethod
    def _section_pairs(context_text: str, title: str, max_pairs: int = 4) -> list:
        """Relaciona encabezados de un material con una evidencia de su propia sección.

        Las presentaciones suelen incluir encabezados como "Evaporación" y después
        varias ideas. Usar esa estructura evita convertir etiquetas decorativas como
        "Etapa 1" o subtítulos de portada en contenido evaluable.
        """
        pairs = []
        current_heading = ''
        ignored_prefixes = ('etapa ', 'material de ', 'ciencias naturales')
        title_lower = str(title or '').strip().lower()

        for raw_line in str(context_text or '').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                current_heading = line.lstrip('#').strip()
                continue
            if not current_heading:
                continue

            point = re.sub(r'^[-*]\s*', '', line).strip()
            heading_lower = current_heading.lower()
            point_lower = point.lower()
            if (
                len(current_heading) < 3
                or current_heading.lower() == title_lower
                or heading_lower.startswith(ignored_prefixes)
                or point_lower.startswith(ignored_prefixes)
                or len(point) < 15
            ):
                continue

            words = point.split()
            concise_point = ' '.join(words[:12]).rstrip('.,;:')
            if len(words) > 12:
                concise_point += '…'
            pairs.append({'left': current_heading, 'right': concise_point})
            current_heading = ''
            if len(pairs) >= max_pairs:
                break

        return pairs if len(pairs) >= 2 else []

    @staticmethod
    def _grounding_error(game: Optional[Dict[str, Any]], source_text: str, game_type: str) -> str:
        """Rechaza estructuras válidas que no aportan evidencia del PPT.

        Un JSON bien formado no basta si, por ejemplo, Matching devuelve
        "Concepto 1". Esta comprobación ligera no añade conocimiento externo:
        exige que la etiqueta evaluable tenga al menos una palabra útil del
        material original.
        """
        if not game:
            return 'No se pudo normalizar la respuesta de Ollama.'
        source_words = set(re.findall(r'\b[a-záéíóúüñ]{4,}\b', source_text.lower()))
        ignored = {
            'concepto', 'conceptos', 'material', 'tema', 'clase', 'actividad',
            'juego', 'parte', 'ciclo', 'agua',
        }

        def grounded(text: Any) -> bool:
            words = set(re.findall(r'\b[a-záéíóúüñ]{4,}\b', str(text or '').lower())) - ignored
            if not words:
                return False
            # A title such as "ciclo del agua" alone is insufficient evidence.
            # Short keywords (for example "evaporación") are valid only when
            # they occur in the material; longer answers must substantially use
            # the vocabulary of an exact PPT statement.
            matches = len(words & source_words)
            return matches >= (1 if len(words) == 1 else max(2, (len(words) * 3 + 3) // 4))

        content = game.get('content') or {}
        if game_type in {'matching', 'memory'}:
            pairs = content.get('pairs') or []
            if any(not grounded(pair.get('left')) for pair in pairs if isinstance(pair, dict)):
                return 'Las parejas no usan conceptos identificables del material docente.'
        elif game_type == 'multiple_choice':
            if not grounded(content.get('answer')):
                return 'La respuesta correcta no contiene evidencia suficiente del material docente.'
            placeholders = {
                'opción correcta', 'opcion correcta', 'distractor 1', 'distractor 2', 'distractor 3',
                'una afirmación breve pero incorrecta', 'otra afirmación breve pero incorrecta',
            }
            raw_options = [str(option or '').strip() for option in (content.get('options') or [])]
            options = {option.lower() for option in raw_options if option}
            if options & placeholders:
                return 'Las alternativas contienen marcadores genéricos y no son aptas para un alumno.'
            if len(raw_options) < 3 or len(options) != len(raw_options):
                return 'Las alternativas deben ser al menos tres y todas diferentes.'
            if any(not grounded(option) for option in raw_options):
                return 'Todas las alternativas deben estar fundamentadas en el material docente.'
            if str(content.get('answer') or '').strip().lower() not in options:
                return 'La respuesta correcta debe coincidir con una alternativa.'
            question = str(content.get('question') or '').strip()
            if question == str(content.get('answer') or '').strip() or '?' not in question:
                return 'La pregunta debe ser una pregunta clara, distinta de la respuesta.'
        elif game_type == 'fill_blank' and not grounded(content.get('blank_word')):
            return 'La palabra a completar no aparece en el material docente.'
        elif game_type == 'true_false' and not grounded(content.get('statement')):
            return 'La afirmación no contiene evidencia suficiente del material docente.'
        elif game_type == 'ordering':
            items = content.get('items') or []
            if any(not grounded(item) for item in items):
                return 'Los pasos para ordenar no usan información identificable del material docente.'
        elif game_type == 'drag_drop':
            items = content.get('items') or []
            if any(not grounded(item.get('item')) for item in items if isinstance(item, dict)):
                return 'Los elementos para clasificar no usan información identificable del material docente.'
        elif game_type == 'challenge':
            levels = content.get('levels') or []
            if any(not grounded(level.get('answer')) for level in levels if isinstance(level, dict)):
                return 'Los niveles no contienen respuestas identificables del material docente.'
        return ''

    @staticmethod
    def _fallback_pairs(title: str, key_points: list, context_text: str = '') -> list:
        """Construye parejas desde frases reales cuando el material no tiene secciones."""
        pairs = []
        points = [str(point).strip() for point in key_points if str(point).strip()]
        if len(points) < 2:
            points = [
                sentence.strip()
                for sentence in re.split(r'[.;]\s*', str(context_text or ''))
                if len(sentence.strip()) >= 15
            ]
        for index, point in enumerate(points[:4], start=1):
            if point.lower().startswith(('etapa ', 'material de ')):
                continue
            words = point.split()
            pairs.append({
                'left': ' '.join(words[:2]).capitalize() or f'Concepto {index}',
                'right': ' '.join(words[2:8]).capitalize() or point[:45],
            })
        if len(pairs) < 2:
            pairs = [
                {'left': f'{title} - idea 1', 'right': 'Fragmento del material'},
                {'left': f'{title} - idea 2', 'right': 'Otro fragmento del material'},
            ]
        return pairs
