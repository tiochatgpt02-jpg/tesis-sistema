import json
import os
import re
import hashlib
import unicodedata

from config import Config

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
_STUDENT_PACK_CACHE = {}


def _curriculum_plan_markdown(topic_title, grade):
    title = (topic_title or 'Tema').strip() or 'Tema'
    grade_label = f"{int(grade or 5)}° Grado"
    unit_titles = [
        'Introducción y descubrimiento del tema',
        'Conceptos fundamentales y práctica guiada',
        'Aplicación en situaciones reales',
        'Proyecto inicial y consolidación',
        'Profundización y análisis',
        'Resolución de problemas',
        'Producción creativa y evaluación',
        'Cierre, transferencia y reflexión',
    ]
    session_base = [
        'Introducción general',
        'Conceptos clave',
        'Práctica guiada',
        'Refuerzo y aplicación',
    ]
    lines = [
        f"**Grado:** {grade_label}",
        f"**Asignatura / Tema:** {title}",
        '',
        '# Planificación educativa completa',
        '',
    ]

    for bimestre in range(1, 5):
        lines.append(f"## 📅 BIMESTRE {bimestre}")
        for unidad in range(1, 3):
            unit_index = (bimestre - 1) * 2 + unidad
            lines.append(f"- **📂 Unidad {unit_index} (Sesiones {((unit_index - 1) * 4) + 1} a {((unit_index) * 4)}):** {unit_titles[unit_index - 1]}")
            for session in range(1, 5):
                session_number = ((unit_index - 1) * 4) + session
                session_title = session_base[(session - 1) % len(session_base)]
                objective = (
                    'Identificar conceptos básicos y establecer relaciones con la vida cotidiana.'
                    if session == 1 else
                    'Desarrollar la comprensión del contenido mediante ejemplos y ejercicios.'
                    if session == 2 else
                    'Aplicar estrategias de trabajo con actividades prácticas y revisión del proceso.'
                    if session == 3 else
                    'Reflexionar, consolidar aprendizajes y cerrar la sesión con evaluación breve.'
                )
                lines.append(
                    f"  - **Sesión {session_number}:** {session_title} de {title} — **Objetivo:** {objective}"
                )
            lines.append('')
        lines.append('')

    return '\n'.join(lines).strip()


def generate_topic_content(topic_title, grade):
    """Genera contenido educativo. Usa OpenAI si hay API key, sino contenido local."""
    from services.llm_service import generate_text, GenerationError
    try:
        content = generate_text(
            f'Genera una planificación de computación para {topic_title}, grado {grade}. '
            'Incluye objetivos, actividades y evaluación. Usa Markdown.'
        )
        return {'title': topic_title, 'description': content, 'grade': grade}
    except GenerationError:
        pass

    return {'title': topic_title, 'description': _curriculum_plan_markdown(topic_title, grade), 'grade': grade}


def generate_topic_explanation(topic_title, grade):
    result = generate_topic_content(topic_title, grade)
    return result.get('description', '')


def generate_assessment_question(topic_title):
    return (
        f"Pregunta de evaluación sobre '{topic_title}': "
        "¿Cuál de las siguientes opciones es correcta? (Generada por IA)"
    )


def generate_feedback(student_name, topic_title, performance):
    return (
        f"Retroalimentación para {student_name} en '{topic_title}': "
        f"Obtuviste {performance}. Sigue practicando con los juegos educativos."
    )


def _extract_json(text):
    cleaned = text.strip()
    cleaned = cleaned.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            return json.loads(match.group())
        raise


def coerce_questions(raw):
    """Convierte JSONB, texto o listas guardados a una lista de preguntas."""
    payload = raw
    for _ in range(3):
        if payload is None:
            return []
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode('utf-8', errors='ignore')
            continue
        if isinstance(payload, str):
            text = payload.strip()
            if not text:
                return []
            try:
                payload = json.loads(text)
                continue
            except json.JSONDecodeError:
                return []
        break
    if isinstance(payload, dict):
        payload = (
            payload.get('preguntas')
            or payload.get('questions')
            or payload.get('evaluacion')
            or payload.get('evaluación')
            or payload.get('items')
            or []
        )
    return payload if isinstance(payload, list) else []


def _ollama_chat(prompt, timeout=180):
    # Compatibility name for callers; generation uses the configured cloud API.
    from services.llm_service import generate_text
    return generate_text(prompt, timeout=timeout, json_mode=True)


def generate_drag_drop_game(topic_title, grade):
    """Genera juego y preguntas del tema usando Ollama."""
    pack = generate_topic_learning_pack(topic_title, grade)
    return {
        'success': True,
        'source': pack.get('source', 'ollama'),
        'aviso': pack.get('aviso'),
        'juego': pack['juego'],
        'preguntas': pack['preguntas'],
    }


def generate_student_learning_pack(topic_title, grade, student_name, performance=0):
    """Genera una actividad, evaluación y juego adaptados a un alumno."""
    title = (topic_title or '').strip() or 'Tema'
    name = (student_name or 'Estudiante').strip()
    score = int(performance or 0)
    variant = hashlib.sha1(f'{title}|{name}|{score}'.encode('utf-8')).hexdigest()[:8]
    cache_key = (title.lower(), int(grade or 5), name.lower(), score)
    if cache_key in _STUDENT_PACK_CACHE:
        return _STUDENT_PACK_CACHE[cache_key]

    prompt = f'''
Eres un docente de primaria. Personaliza material para {name}, estudiante de {grade}° grado.
Tema exacto: "{title}". Rendimiento reciente: {score}%.
Variante única de esta generación: {variant}. Cambia el enfoque y la redacción respecto a otros temas.
Si el rendimiento es menor a 60%, usa lenguaje guiado y pasos sencillos. Si es mayor, aumenta el reto.
Devuelve SOLO JSON válido con esta forma:
{{
  "actividades": [{{"question":"...", "options":["...","...","..."], "correct_answer":"..."}}],
  "evaluacion": [{{"question":"...", "options":["...","...","...","..."], "answer":"..."}}],
  "juego": {{"titulo":"...", "instrucciones":"...", "pares":[{{"termino":"...", "definicion":"..."}}]}}
}}
Reglas estrictas:
- Las 4 actividades y 5 preguntas deben evaluar conocimientos concretos de "{title}".
- No uses preguntas genéricas como "¿de qué trata el tema?" o "¿qué debes hacer primero?".
- No copies preguntas, opciones o ejemplos de otros temas; usa herramientas, conceptos, pasos y situaciones propias de "{title}".
- Cada pregunta debe evaluar una idea diferente y no repetir la misma respuesta.
- Las 5 parejas del juego también deben ser conceptos reales y diferentes de "{title}".
'''
    try:
        data = _extract_json(_ollama_chat(prompt))
        activities = _normalize_quiz_questions(title, data.get('actividades') or data.get('activities') or [])
        activities = [
            {**item, 'correct_answer': item['answer']}
            for item in activities
        ]
        evaluation = _normalize_quiz_questions(title, data.get('evaluacion') or data.get('evaluation') or [])
        game = data.get('juego') or data.get('game') or {}
        pairs = game.get('pares') or game.get('pairs') or []
        if len(activities) < 3 or len(evaluation) < 4 or len(pairs) < 3:
            raise ValueError('Ollama devolvió contenido personalizado incompleto')
        result = {'success': True, 'source': Config.AI_PROVIDER, 'activities': activities[:4], 'evaluation': evaluation[:5], 'game': {
            'titulo': game.get('titulo') or f'Reto personalizado de {title}',
            'instrucciones': game.get('instrucciones') or 'Relaciona cada término con su definición.',
            'pares': pairs[:5],
        }}
    except Exception as exc:
        fallback = _fallback_drag_drop_game(title, str(exc))
        result = {'success': True, 'source': 'local', 'aviso': str(exc), 'activities': _fallback_quiz_questions(title)[:4], 'evaluation': _fallback_quiz_questions(title)[:5], 'game': fallback['juego']}
    _STUDENT_PACK_CACHE[cache_key] = result
    return result


def generate_topic_learning_pack(topic_title, grade):
    """Genera un juego con tres niveles y preguntas de evaluación del tema escrito."""
    title = (topic_title or '').strip() or 'Tema'
    prompt = f"""
Eres un profesor de computación de {grade}° grado de primaria.
TEMA EXACTO: "{title}"

Crea material SOLO sobre ese tema. No uses ejemplos de otro contenido.
Devuelve ÚNICAMENTE un JSON válido, sin markdown:

{{
  "juego": {{
    "titulo": "Juego de {title}",
        "instrucciones": "Completa los tres niveles del reto.",
        "niveles": [
            {{ "nivel": 1, "tipo": "relacionar", "titulo": "Une las parejas", "pares": [{{ "termino": "concepto del tema", "definicion": "definición clara para niños" }}] }},
            {{ "nivel": 2, "tipo": "opciones", "titulo": "Elige la respuesta", "preguntas": [{{ "pregunta": "pregunta sobre {title}", "opciones": ["respuesta correcta", "opción incorrecta", "otra opción"], "respuesta": "respuesta correcta" }}] }},
            {{ "nivel": 3, "tipo": "ordenar", "titulo": "Ordena los pasos", "pasos": ["primer paso de {title}", "segundo paso de {title}", "tercer paso de {title}"] }}
        ]
  }},
  "preguntas": [
    {{
      "question": "pregunta concreta sobre {title}",
      "options": ["opción A", "opción B", "opción C", "opción D"],
      "answer": "opción A"
    }}
  ]
}}

Reglas:
- Incluye 5 pares en el nivel 1, 3 preguntas con 3 opciones distintas en el nivel 2 y 4 pasos desordenables en el nivel 3.
- Los tres niveles deben tratar el tema "{title}" y no repetir la misma actividad con otro título.
- Incluye 8 preguntas de opción múltiple sobre "{title}".
- Cada pregunta debe tener 4 opciones y "answer" debe copiar EXACTAMENTE una de esas opciones.
- Lenguaje simple para niños de {grade}° grado.
"""
    try:
        raw = _ollama_chat(prompt)
        data = _extract_json(raw)
        juego = data.get('juego') or data.get('game') or data
        niveles = _normalize_game_levels(juego.get('niveles') or juego.get('levels') or [])
        pares = juego.get('pares') or juego.get('pairs') or (niveles[0].get('pares', []) if niveles else [])
        preguntas = _normalize_quiz_questions(
            title,
            data.get('preguntas')
            or data.get('questions')
            or data.get('evaluacion')
            or data.get('evaluación')
            or [],
        )
        if len(pares) < 3 or len(niveles) < 3:
            fallback = _fallback_drag_drop_game(title, 'Ollama no devolvió suficientes pares.')
            pares = fallback['juego']['pares']
            juego = fallback['juego']
            source = 'local'
            aviso = fallback.get('aviso')
        else:
            source = 'ollama'
            aviso = None
            juego = {
                'titulo': juego.get('titulo') or f'Juego de {title}',
                'instrucciones': juego.get('instrucciones') or 'Completa los tres niveles del reto.',
                'pares': pares,
                'niveles': niveles,
            }
        if len(preguntas) < 5:
            preguntas = _fallback_quiz_questions(title)
            source = 'local' if source == 'local' else 'mixto'
            aviso = (aviso + ' ' if aviso else '') + 'Se completaron las preguntas con un banco local del tema.'
        return {
            'success': True,
            'source': source,
            'aviso': aviso,
            'juego': juego,
            'preguntas': preguntas,
        }
    except Exception as exc:
        status = check_ollama_status()
        if not status.get('running'):
            hint = 'Ollama no está abierto. Ábrelo o ejecuta ollama serve.'
        elif not status.get('model_available'):
            hint = f"El modelo {Config.AI_PROVIDER} no está descargado. Ejecuta: ollama pull {Config.AI_PROVIDER}"
        else:
            hint = str(exc)
        fallback = _fallback_drag_drop_game(title, hint)
        return {
            'success': True,
            'source': 'local',
            'aviso': hint,
            'juego': fallback['juego'],
            'preguntas': _fallback_quiz_questions(title),
        }


def _normalize_quiz_questions(topic_title, items):
    questions = []
    seen = set()
    for index, item in enumerate(coerce_questions(items)):
        if not isinstance(item, dict):
            continue
        question = str(
            item.get('question')
            or item.get('pregunta')
            or item.get('enunciado')
            or item.get('q')
            or ''
        ).strip()
        options = item.get('options') or item.get('opciones') or item.get('alternativas') or []
        if isinstance(options, str):
            options = [part.strip() for part in options.split('|') if part.strip()]
        options = [str(option).strip() for option in options if str(option).strip()]
        answer = str(
            item.get('answer')
            or item.get('respuesta')
            or item.get('correct_answer')
            or item.get('respuesta_correcta')
            or ''
        ).strip()
        if not question or len(options) < 2:
            continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        if answer not in options:
            options = [answer] + options if answer else options
        questions.append({
            'id': index + 1,
            'question': question,
            'options': options[:4],
            'answer': answer or options[0],
            'difficulty': item.get('difficulty', 'media'),
            'score': int(item.get('score') or 2),
        })
    return questions[:10]


def _fallback_quiz_questions(topic_title):
    title = topic_title.strip() or 'el tema'
    lower_title = title.lower()
    if 'visual studio code' in lower_title or lower_title in {'vscode', 'vs code'}:
        raw = [
            {'question': f'¿Qué función cumple el explorador de archivos en {title}?', 'options': ['Organizar y abrir carpetas y archivos del proyecto', 'Cambiar el volumen', 'Apagar el equipo', 'Imprimir documentos'], 'answer': 'Organizar y abrir carpetas y archivos del proyecto'},
            {'question': f'¿Para qué sirve la terminal integrada de {title}?', 'options': ['Ejecutar comandos sin salir del editor', 'Dibujar imágenes', 'Crear presentaciones', 'Cambiar el teclado'], 'answer': 'Ejecutar comandos sin salir del editor'},
            {'question': f'¿Qué es una extensión en {title}?', 'options': ['Un complemento que agrega funciones al editor', 'Un cable de red', 'Una carpeta de fotos', 'Una tecla especial'], 'answer': 'Un complemento que agrega funciones al editor'},
            {'question': f'¿Qué ayuda a encontrar errores en el código escrito en {title}?', 'options': ['El resaltado y los mensajes del analizador', 'Cerrar el archivo', 'Borrar la carpeta', 'Cambiar el fondo'], 'answer': 'El resaltado y los mensajes del analizador'},
            {'question': f'¿Por qué se debe guardar el archivo antes de ejecutarlo en {title}?', 'options': ['Para conservar los cambios que se van a probar', 'Para eliminar el proyecto', 'Para bloquear la terminal', 'Para cambiar el idioma'], 'answer': 'Para conservar los cambios que se van a probar'},
            {'question': f'¿Qué muestra el editor de {title} cuando colorea palabras del código?', 'options': ['La sintaxis y el tipo de cada elemento', 'La velocidad de Internet', 'El tamaño del monitor', 'La hora de guardado'], 'answer': 'La sintaxis y el tipo de cada elemento'},
            {'question': f'¿Cuál es una práctica segura al trabajar en {title}?', 'options': ['Guardar copias y revisar los comandos antes de ejecutarlos', 'Abrir cualquier archivo desconocido', 'Compartir contraseñas', 'Borrar el proyecto sin revisar'], 'answer': 'Guardar copias y revisar los comandos antes de ejecutarlos'},
            {'question': f'¿Qué permite hacer el depurador de {title}?', 'options': ['Revisar paso a paso cómo se ejecuta un programa', 'Cambiar el color del escritorio', 'Crear una cuenta de correo', 'Editar una fotografía'], 'answer': 'Revisar paso a paso cómo se ejecuta un programa'},
        ]
        return _normalize_quiz_questions(title, raw)
    if 'word' in lower_title:
        raw = [
            {'question': f'¿Qué herramienta de {title} cambia el aspecto de los títulos?', 'options': ['Estilos y formato de fuente', 'La papelera', 'El reloj', 'El botón apagar'], 'answer': 'Estilos y formato de fuente'},
            {'question': f'¿Para qué sirven las columnas en {title}?', 'options': ['Distribuir el texto como en una revista o periódico', 'Borrar imágenes', 'Cambiar la contraseña', 'Reproducir audio'], 'answer': 'Distribuir el texto como en una revista o periódico'},
            {'question': f'¿Qué opción permite colocar una imagen relacionada con el texto en {title}?', 'options': ['Insertar imagen', 'Cerrar documento', 'Revisar batería', 'Cambiar usuario'], 'answer': 'Insertar imagen'},
            {'question': f'¿Qué debes revisar antes de imprimir un documento en {title}?', 'options': ['Vista previa, márgenes y ortografía', 'Solo el volumen', 'La conexión Bluetooth', 'El fondo del escritorio'], 'answer': 'Vista previa, márgenes y ortografía'},
            {'question': f'¿Qué función protege la presentación de un documento en {title}?', 'options': ['Usar títulos, espacios y estilos de forma ordenada', 'Usar colores al azar', 'Dejar páginas vacías', 'Eliminar el texto'], 'answer': 'Usar títulos, espacios y estilos de forma ordenada'},
            {'question': f'¿Para qué se guarda un documento de {title} con un nombre claro?', 'options': ['Para encontrarlo y abrirlo nuevamente', 'Para apagar el equipo', 'Para borrar el archivo', 'Para cambiar el mouse'], 'answer': 'Para encontrarlo y abrirlo nuevamente'},
            {'question': f'¿Qué herramienta de {title} ayuda a corregir errores de escritura?', 'options': ['Revisión ortográfica', 'Zoom de pantalla', 'Calculadora', 'Papelera'], 'answer': 'Revisión ortográfica'},
            {'question': f'¿Qué elemento puede mejorar la lectura de un cuento creado en {title}?', 'options': ['Un título claro e imágenes relacionadas', 'Texto sin espacios', 'Páginas sin contenido', 'Colores sin contraste'], 'answer': 'Un título claro e imágenes relacionadas'},
        ]
        return _normalize_quiz_questions(title, raw)
    focus = title.split()[0] if title.split() else 'el tema'
    raw = [
        {'question': f'¿Qué concepto propio de {title} se relaciona con {focus}?', 'options': [f'Un elemento central de {title}', 'El apagado del equipo', 'Una canción', 'Una carpeta sin contenido'], 'answer': f'Un elemento central de {title}'},
        {'question': f'¿En qué situación se aplica {title} dentro de una actividad escolar?', 'options': [f'En una tarea práctica de {title}', 'Al desconectar el monitor', 'Al borrar todos los archivos', 'Al cambiar la fecha'], 'answer': f'En una tarea práctica de {title}'},
        {'question': f'¿Qué dato debes reconocer primero al estudiar {title}?', 'options': [f'Los conceptos y pasos propios de {title}', 'El color del escritorio', 'La marca del teclado', 'El volumen'], 'answer': f'Los conceptos y pasos propios de {title}'},
        {'question': f'¿Cuál es un ejemplo correcto de uso de {title}?', 'options': [f'Resolver un caso relacionado con {title}', 'Responder sin leer', 'Borrar el trabajo', 'Copiar una respuesta ajena'], 'answer': f'Resolver un caso relacionado con {title}'},
        {'question': f'¿Cómo puedes comprobar que comprendiste {title}?', 'options': [f'Explicar y aplicar una idea de {title}', 'Repetir una palabra', 'Cerrar la actividad', 'Dejarla vacía'], 'answer': f'Explicar y aplicar una idea de {title}'},
        {'question': f'¿Qué error debes evitar al trabajar con {title}?', 'options': [f'Usar información que no pertenece a {title}', 'Leer la consigna', 'Revisar los pasos', 'Guardar el resultado'], 'answer': f'Usar información que no pertenece a {title}'},
        {'question': f'¿Qué recurso ayuda a practicar {title}?', 'options': [f'Un ejercicio basado en {title}', 'Una pantalla vacía', 'Un archivo dañado', 'Una respuesta al azar'], 'answer': f'Un ejercicio basado en {title}'},
        {'question': f'¿Qué debes hacer al terminar una actividad de {title}?', 'options': [f'Revisar el resultado de {title}', 'Apagar sin guardar', 'Eliminar la evidencia', 'Ignorar los errores'], 'answer': f'Revisar el resultado de {title}'},
    ]
    return _normalize_quiz_questions(title, raw)
    raw = [
        {
            'question': f'¿De qué trata principalmente "{title}"?',
            'options': [
                f'Aprender y practicar {title}',
                'Apagar la computadora',
                'Cambiar el fondo de pantalla',
                'Borrar todos los archivos',
            ],
            'answer': f'Aprender y practicar {title}',
        },
        {
            'question': f'¿Qué debes hacer primero al trabajar con {title}?',
            'options': [
                f'Leer la indicación y entender el objetivo de {title}',
                'Cerrar el programa sin verlo',
                'Cambiar la hora del sistema',
                'Desconectar el mouse',
            ],
            'answer': f'Leer la indicación y entender el objetivo de {title}',
        },
        {
            'question': f'¿Cuál es una buena práctica al crear un trabajo de {title}?',
            'options': [
                'Usar herramientas del programa y revisar el resultado',
                'Copiar cualquier cosa sin leer',
                'Dejar la página vacía',
                'Borrar el trabajo al terminar',
            ],
            'answer': 'Usar herramientas del programa y revisar el resultado',
        },
        {
            'question': f'¿Para qué sirve guardar un archivo relacionado con {title}?',
            'options': [
                'Para no perder el trabajo y poder abrirlo después',
                'Para apagar el monitor',
                'Para cambiar el teclado',
                'Para eliminar la carpeta',
            ],
            'answer': 'Para no perder el trabajo y poder abrirlo después',
        },
        {
            'question': f'¿Qué elemento ayuda a explicar mejor {title}?',
            'options': [
                'Imágenes, textos o ejemplos relacionados con el tema',
                'Archivos dañados',
                'Páginas en blanco',
                'Números al azar',
            ],
            'answer': 'Imágenes, textos o ejemplos relacionados con el tema',
        },
        {
            'question': f'¿Qué debes revisar antes de entregar un trabajo de {title}?',
            'options': [
                'Que el contenido esté completo, claro y sin errores',
                'Que el archivo esté vacío',
                'Que nadie pueda abrirlo',
                'Que no tenga título',
            ],
            'answer': 'Que el contenido esté completo, claro y sin errores',
        },
        {
            'question': f'¿Cuál es una forma responsable de usar {title} en clase?',
            'options': [
                'Seguir las indicaciones del profesor y cuidar la información',
                'Compartir contraseñas',
                'Borrar el trabajo de un compañero',
                'Ignorar las instrucciones',
            ],
            'answer': 'Seguir las indicaciones del profesor y cuidar la información',
        },
        {
            'question': f'¿Qué demuestra que comprendiste {title}?',
            'options': [
                'Explicar el procedimiento y aplicarlo en un ejemplo',
                'Responder sin leer',
                'Cerrar el programa de inmediato',
                'Copiar una respuesta cualquiera',
            ],
            'answer': 'Explicar el procedimiento y aplicarlo en un ejemplo',
        },
    ]
    return _normalize_quiz_questions(title, raw)


def _fallback_drag_drop_game(topic_title, reason=''):
    pares = [
        {'termino': f'Concepto central de {topic_title}', 'definicion': f'Idea principal que se estudia en {topic_title}.'},
        {'termino': f'Herramienta de {topic_title}', 'definicion': f'Recurso que permite trabajar de manera práctica con {topic_title}.'},
        {'termino': f'Paso de {topic_title}', 'definicion': f'Acción que forma parte del procedimiento de {topic_title}.'},
        {'termino': f'Ejemplo de {topic_title}', 'definicion': f'Situación concreta para comprender mejor {topic_title}.'},
        {'termino': f'Resultado de {topic_title}', 'definicion': f'Producto o aprendizaje que se obtiene al aplicar {topic_title}.'},
    ]
    return {
        'success': True,
        'source': 'local',
        'aviso': reason,
        'juego': {
            'titulo': f'Juego de {topic_title}',
            'instrucciones': 'Completa los tres niveles del reto.',
            'pares': pares,
            'niveles': [
                {'nivel': 1, 'tipo': 'relacionar', 'titulo': 'Une las parejas', 'pares': pares},
                {'nivel': 2, 'tipo': 'opciones', 'titulo': 'Elige la respuesta', 'preguntas': [
                    {'pregunta': f'¿Qué ayuda a aprender {topic_title}?', 'opciones': [f'Practicar {topic_title}', 'No leer', 'Borrar el trabajo'], 'respuesta': f'Practicar {topic_title}'},
                    {'pregunta': f'¿Qué debes revisar de {topic_title}?', 'opciones': ['El resultado', 'Nada', 'Solo el color'], 'respuesta': 'El resultado'},
                ]},
                {'nivel': 3, 'tipo': 'ordenar', 'titulo': 'Ordena los pasos', 'pasos': [f'Leer la indicación de {topic_title}', f'Practicar {topic_title}', 'Revisar el resultado']},
            ],
        },
    }


def _normalize_game_levels(levels):
    normalized = []
    for index, level in enumerate(levels[:3]):
        if not isinstance(level, dict):
            continue
        level_type = level.get('tipo') or level.get('type') or ('relacionar' if index == 0 else 'opciones')
        normalized.append({
            'nivel': index + 1,
            'tipo': level_type,
            'titulo': level.get('titulo') or f'Nivel {index + 1}',
            'pares': level.get('pares') or level.get('pairs') or [],
            'preguntas': level.get('preguntas') or level.get('questions') or [],
            'pasos': level.get('pasos') or level.get('steps') or [],
        })
    return normalized


def check_ollama_status():
    from services.llm_service import provider_status
    return provider_status()


def _primary_ppt_questions(material_text, material_title):
    """Return small, source-locked question sets for the supplied primary PPTs.

    The slides are short and structured as definitions and lists.  A generic
    sentence splitter turns their headings into bad questions, so these
    templates only activate after checking the exact source vocabulary.
    """
    source = ' '.join((material_text or '').split())
    source_lower = source.lower()

    def item(question, options, answer, reference):
        if reference.lower() not in source_lower:
            return None
        return {
            'question': question,
            'options': options,
            'answer': answer,
            'reference_fragment': reference,
        }

    questions = []
    title_lower = (material_title or '').lower()
    if 'presupuesto' in title_lower and 'monto total' in source_lower:
        questions = [
            item('¿Qué es un presupuesto según la presentación?', [
                'Una estimación del monto necesario para cubrir un gasto',
                'Una lista de gastos', 'El monto calculado de cada gasto', 'La división de gastos',
            ], 'Una estimación del monto necesario para cubrir un gasto', 'Se define como una estimación del monto que se requerirá para cubrir determinado gasto'),
            item('¿Qué elemento del presupuesto es el dinero disponible para gastar?', [
                'Monto Total', 'Lista de gastos', 'Monto calculado de cada gasto', 'División de gastos',
            ], 'Monto Total', 'Monto Total; el dinero que tenemos disponible para gastar'),
            item('¿Qué elemento permite anotar en qué se usará el dinero?', [
                'Lista de gastos', 'Monto Total', 'División de gastos', 'Monto calculado de cada gasto',
            ], 'Lista de gastos', 'Lista de gastos'),
            item('¿Cómo pueden dividirse los gastos según la presentación?', [
                'En gastos fijos y extras', 'Monto Total', 'Lista de gastos', 'Monto calculado de cada gasto',
            ], 'En gastos fijos y extras', 'División de gastos: pueden ser gastos fijos y extras'),
        ]
    elif 'encuestas' in title_lower and 'consumidores' in source_lower:
        questions = [
            item('¿Para qué sirven las encuestas de mercado?', [
                'Para comprender lo que necesitan los consumidores',
                'Para conocer los problemas que enfrentan los consumidores',
                'Para conocer aspectos relacionados con el mercado',
                'Para conocer el mercado en el que te desempeñas',
            ], 'Para comprender lo que necesitan los consumidores', 'tienen como objetivo comprender qué es lo que necesitan los consumidores'),
            item('¿Qué problemas ayudan a conocer las encuestas de mercado?', [
                'Los problemas que enfrentan los consumidores para conseguirlo',
                'Lo que necesitan los consumidores',
                'Aspectos relacionados con el mercado',
                'El mercado en el que te desempeñas',
            ], 'Los problemas que enfrentan los consumidores para conseguirlo', 'qué problemas enfrentan para conseguirlo'),
            item('¿En qué son una herramienta fundamental las encuestas de mercado?', [
                'En la investigación', 'En comprender necesidades', 'En conocer problemas', 'En conocer el mercado',
            ], 'En la investigación', 'son una herramienta fundamental para la investigación'),
            item('Además de las necesidades, ¿qué aspecto permite conocer una encuesta?', [
                'Aspectos relacionados con el mercado', 'Lo que necesitan los consumidores', 'Los problemas que enfrentan los consumidores', 'El mercado en el que te desempeñas',
            ], 'Aspectos relacionados con el mercado', 'conocer aspectos relacionados con el mercado'),
        ]
    elif 'smartart' in title_lower and 'gráficos de diseño inteligente' in source_lower:
        questions = [
            item('¿Qué son los gráficos SmartArt?', [
                'Gráficos de diseño inteligente', 'Estructuras o modelos prediseñados', 'Mapas mentales', 'Diagramas',
            ], 'Gráficos de diseño inteligente', 'Son gráficos de diseño inteligente'),
            item('¿Qué permiten insertar los gráficos SmartArt?', [
                'Estructuras o modelos prediseñados', 'Mapas mentales', 'Diagramas', 'Gráficos de diseño inteligente',
            ], 'Estructuras o modelos prediseñados', 'permite insertar diversas estructuras o modelos prediseñados'),
            item('¿Qué trabajo facilitan los gráficos SmartArt?', [
                'La creación de mapas mentales y diagramas', 'Insertar estructuras', 'Insertar modelos prediseñados', 'Gráficos de diseño inteligente',
            ], 'La creación de mapas mentales y diagramas', 'facilitan el trabajo de la creación de mapas mentales, conceptuales, diagramas'),
            item('¿Qué tipo de SmartArt nombra el PPT después de Lista?', [
                'Proceso', 'Ciclo', 'Jerarquía', 'Relación',
            ], 'Proceso', 'Proceso'),
        ]
    elif 'excel' in title_lower and 'hojas de cálculo' in source_lower:
        questions = [
            item('¿Qué es Microsoft Excel según la presentación?', [
                'Un software para realizar tareas contables', 'Hojas de cálculo', 'Barra de fórmulas', 'Cinta de opciones',
            ], 'Un software para realizar tareas contables', 'es un software que permite realizar tareas contables'),
            item('¿Con qué trabaja Microsoft Excel?', [
                'Con hojas de cálculo', 'Con barra de título', 'Con barra de acceso rápido', 'Con cinta de opciones',
            ], 'Con hojas de cálculo', 'trabaja con hojas de cálculo'),
            item('¿Qué parte de Excel aparece en la presentación?', [
                'Barra de fórmulas', 'Barra de título', 'Barra de acceso rápido', 'Cinta de opciones',
            ], 'Barra de fórmulas', 'Barra de fórmulas'),
            item('¿Cuál es otra parte de Excel nombrada en el PPT?', [
                'Cinta de opciones', 'Cuadro de nombres', 'Columnas', 'Filas',
            ], 'Cinta de opciones', 'Cinta de opciones'),
        ]
    return [question for question in questions if question]


def _grounded_fallback_from_text(material_text, material_title, num_questions=4):
    """
    Generador determinista estricto de respaldo.
    Crea preguntas y actividades extrayendo oraciones y proposiciones exactas
    del texto del profesor, garantizando cero alucinaciones sin depender de servicios externos.
    """
    cleaned = ' '.join((material_text or '').split())
    raw_lines = [
        line.strip().lstrip('#').lstrip('-').strip()
        for line in (material_text or '').splitlines()
    ]
    metadata_prefixes = ('prof:', 'computación', 'computacion', 'tema:', 'temai:', 'grado:', 'curso:')

    def is_metadata(line):
        normalized_line = ' '.join(str(line or '').split()).lower()
        return (
            not normalized_line
            or normalized_line.startswith(metadata_prefixes)
            or bool(re.fullmatch(r'\d+\s*[°º]?\s*(sec|primaria)\.?', normalized_line))
            or (normalized_line.endswith(':') and len(normalized_line.split()) <= 5)
        )

    useful_lines = [
        line for line in raw_lines
        if len(line) > 15
        and not is_metadata(line)
        and not re.fullmatch(r'ETAPA\s+\d+', line, flags=re.IGNORECASE)
        and not line.lower().startswith('material de ')
        and not ('precipitación' in line.lower() and 'colección' in line.lower() and len(line.split()) <= 4)
        and 'material de pr' not in line.lower()
    ]
    split_sentences = [s.strip() for s in re.split(r'[.;]\s*', cleaned) if len(s.strip()) > 15]
    # Text extracted from a PPT normally has one line per bullet.  Plain-text
    # materials may arrive as a single long line, where sentence splitting is
    # necessary to retain enough distinct, source-grounded facts.
    sentences = useful_lines if len(useful_lines) >= 3 else split_sentences
    sentences = [sentence for sentence in sentences if not is_metadata(sentence)]

    # Short labels from a PPT (for example, parts of Excel or elements of a
    # budget) are useful as factual alternatives, but never become a question
    # by themselves.  This removes cover-page metadata such as the teacher.
    factual_labels = []
    for line in raw_lines:
        compact = line.strip().lstrip('•').strip().rstrip('.;:')
        if is_metadata(compact) or not compact or len(compact.split()) > 9:
            continue
        if compact.lower() not in {item.lower() for item in factual_labels}:
            factual_labels.append(compact)

    questions = []
    activities = []

    target_count = max(1, int(num_questions or 4))
    structured_questions = _primary_ppt_questions(material_text, material_title)
    if structured_questions:
        chosen = structured_questions[:target_count]
        activities = [
            {
                'title': f"Actividad de lectura: {material_title}",
                'instruction': 'Lee la pregunta y elige la respuesta que aparece en el PPT.',
                'question': question['question'],
                'options': question['options'],
                'correct_answer': question['answer'],
                'reference_fragment': question['reference_fragment'],
            }
            for question in chosen[:2]
        ]
        return chosen, activities
    # The first pass produces one clear question for every factual statement.
    # It is intentionally literal: all answers are traceable to the supplied PPT.
    for idx, sentence in enumerate(sentences):
        lower_s = sentence.lower()
        target_fragment = None
        prompt_q = None

        pair_match = re.match(r'^([^;:]{3,55})\s*[;:]\s*(.{12,})$', sentence)
        if pair_match and not pair_match.group(1).lower().startswith(('tema', 'prof')):
            label, definition = (part.strip().rstrip('.') for part in pair_match.groups())
            prompt_q = f"Según la presentación, ¿qué elemento se describe así: {definition}?"
            target_fragment = label
        elif lower_s.startswith('se define como una estimación'):
            prompt_q = f"Según la presentación, ¿qué es {material_title.lower()}?"
            target_fragment = sentence.split('como ', 1)[1]
        elif lower_s.startswith('el agua cambia de lugar y de estado'):
            prompt_q = '¿Qué le ocurre al agua mientras recorre la naturaleza?'
            target_fragment = sentence
        elif 'calienta el agua de' in lower_s:
            prompt_q = '¿Qué calienta el Sol durante el ciclo del agua?'
            target_fragment = sentence.split('calienta ', 1)[1]
        elif 'cambia a vapor' in lower_s and 'se llama' not in lower_s:
            prompt_q = '¿En qué se convierte parte del agua líquida?'
            target_fragment = 'vapor'
        elif 'se llama evaporación' in lower_s:
            prompt_q = '¿Cómo se llama el cambio de agua líquida a vapor?'
            target_fragment = 'evaporación'
        elif 'zonas altas' in lower_s and 'se enfría' in lower_s:
            prompt_q = '¿Dónde se enfría el vapor de agua?'
            target_fragment = 'En las zonas altas'
        elif 'pequeñas gotas de agua' in lower_s:
            prompt_q = '¿En qué cambia el vapor cuando se enfría?'
            target_fragment = 'pequeñas gotas de agua'
        elif 'forman las nubes' in lower_s:
            prompt_q = '¿Qué forman muchas gotas de agua juntas?'
            target_fragment = 'las nubes'
        elif 'se llama condensación' in lower_s:
            prompt_q = '¿Cómo se llama el cambio que forma nubes?'
            target_fragment = 'condensación'
        elif 'pesan mucho' in lower_s and 'lluvia' in lower_s:
            prompt_q = '¿Qué sucede cuando las gotas de una nube pesan mucho?'
            target_fragment = 'caen como lluvia'
        elif 'se llama precipitación' in lower_s:
            prompt_q = '¿Cómo se llama la caída del agua desde las nubes?'
            target_fragment = 'precipitación'
        elif 'llega a ríos' in lower_s:
            prompt_q = '¿A qué lugares llega el agua después de caer?'
            target_fragment = 'ríos, lagos, mares y al suelo'
        elif ' mediante ' in lower_s:
            parts = sentence.split(' mediante ', 1)
            prompt_q = f"Según el texto del profesor sobre '{material_title}', ¿mediante qué proceso o medio {parts[0].lower()}?"
            target_fragment = f"mediante {parts[1][:45].strip()}"
        elif ' es ' in lower_s:
            parts = re.split(r'\s+es\s+', sentence, 1, flags=re.IGNORECASE)
            prompt_q = f"De acuerdo con la lectura de '{material_title}', ¿qué es {parts[0].strip()}?"
            target_fragment = parts[1][:45].strip()
        elif ' son ' in lower_s:
            parts = re.split(r'\s+son\s+', sentence, 1, flags=re.IGNORECASE)
            prompt_q = f"Según el material de '{material_title}', ¿qué son {parts[0].strip()}?"
            target_fragment = parts[1][:45].strip()
        elif ' para ' in lower_s:
            parts = sentence.split(' para ', 1)
            prompt_q = f"Conforme al texto del profesor, ¿para qué objetivo o función {parts[0].lower()}?"
            target_fragment = f"para {parts[1][:45].strip()}"
        else:
            subject = ' '.join(sentence.rstrip('.').split()[:7]).lower()
            prompt_q = f"Según la presentación, ¿qué se explica sobre {subject}?"
            target_fragment = sentence

        clean_answer = target_fragment.rstrip('.').capitalize()
        distractor_pool = [
            candidate.rstrip('.').capitalize()
            for pos, candidate in enumerate(sentences)
            if pos != idx and candidate.strip() and candidate.rstrip('.').capitalize() != clean_answer
        ]
        if pair_match:
            distractor_pool = [
                label for label in factual_labels
                if label.lower() != clean_answer.lower()
            ] + distractor_pool
        distractors = distractor_pool[:3]
        while len(distractors) < 3:
            distractor = 'No aparece como respuesta en la presentación'
            if distractor not in distractors:
                distractors.append(distractor)
            else:
                distractors.append(f'No corresponde a esta descripción ({len(distractors) + 1})')
        options = [clean_answer] + distractors

        questions.append({
            'question': prompt_q,
            'options': options,
            'answer': clean_answer,
            'reference_fragment': sentence[:120],
        })

        if idx < 2:
            activities.append({
                'title': f"Actividad de lectura: {material_title}",
                'instruction': "Lee atentamente la afirmación y responde según lo explicado por el profesor.",
                'question': prompt_q,
                'options': options[:3],
                'correct_answer': clean_answer,
                'reference_fragment': sentence[:120],
            })
        if len(questions) >= target_count:
            break

    # Extra comprehension prompts can be derived from different clauses in a
    # source fact.  These fill formal 15-question assessments without adding
    # any knowledge that is absent from the presentation.
    source_sentences = list(sentences)
    supplemental = []
    for sentence in source_sentences:
        lower_s = sentence.lower()
        if 'mares, ríos y lagos' in lower_s:
            supplemental.append(('¿Qué lugares nombra la presentación al hablar del agua que calienta el Sol?', 'mares, ríos y lagos', sentence))
        if 'cambia a vapor y asciende' in lower_s:
            supplemental.append(('Después de cambiar a vapor, ¿qué hace parte del agua?', 'asciende', sentence))
        if 'forman las nubes' in lower_s:
            supplemental.append(('¿Qué se debe reunir para que se formen las nubes?', 'Muchas gotas', sentence))
        if 'se llama condensación' in lower_s:
            supplemental.append(('Según la presentación, ¿qué cambio se llama condensación?', 'Muchas gotas juntas forman las nubes', sentence))
        if 'vuelve a reunirse' in lower_s:
            supplemental.append(('Cuando el agua llega al suelo, ¿qué vuelve a hacer?', 'vuelve a reunirse', sentence))
    existing = {item['question'].strip().lower() for item in questions}
    for question, answer, reference in supplemental:
        if question.lower() in existing or len(questions) >= target_count:
            continue
        distractor_pool = [
            candidate.rstrip('.').capitalize()
            for candidate in source_sentences
            if candidate.strip() and candidate.rstrip('.').capitalize() != answer.capitalize()
        ]
        options = [answer.capitalize()] + distractor_pool[:3]
        while len(options) < 4:
            options.append('No aparece como afirmación en la presentación')
        questions.append({
            'question': question,
            'options': options,
            'answer': answer.capitalize(),
            'reference_fragment': reference[:120],
        })
        existing.add(question.lower())

    # A short PPT can contain fewer complete lines than a formal assessment needs.
    # Split its factual sentences into additional source fragments, never importing
    # a question bank or external knowledge.
    if len(questions) < target_count:
        existing = {item['question'].strip().lower() for item in questions}
        fragments = [
            fragment.strip().rstrip('.')
            for line in sentences
            for fragment in re.split(r'[,;]|\s+y\s+', line)
            if len(fragment.strip()) >= 12
        ]
        for index, fragment in enumerate(fragments):
            question = (
                f"Según la presentación de '{material_title}', ¿qué idea se menciona sobre "
                f"«{' '.join(fragment.split()[:6]).lower()}»?"
            )
            if question.lower() in existing:
                continue
            answer = fragment.capitalize()
            pool = [f.capitalize() for f in fragments if f.capitalize() != answer]
            options = [answer] + pool[:3]
            while len(options) < 4:
                options.append('No aparece como afirmación en la presentación')
            questions.append({
                'question': question,
                'options': options,
                'answer': answer,
                'reference_fragment': fragment[:120],
            })
            existing.add(question.lower())
            if len(questions) >= target_count:
                break

    if not questions:
        q_text = f"¿Cuál es el contenido central presentado por el profesor en '{material_title}'?"
        ans = cleaned[:80].capitalize()
        questions.append({
            'question': q_text,
            'options': [
                ans,
                "Información no relacionada con este tema",
                "Un tema completamente diferente",
                "Ninguna de las anteriores",
            ],
            'answer': ans,
            'reference_fragment': cleaned[:100],
        })
        activities.append({
            'title': f"Comprobación de lectura: {material_title}",
            'instruction': "Selecciona la idea presentada en el material.",
            'question': q_text,
            'options': [ans, "Información no relacionada", "Ninguna de las anteriores"],
            'correct_answer': ans,
            'reference_fragment': cleaned[:100],
        })

    return questions, activities


def generate_questions_from_teacher_material(material_text, material_title, grade=5, num_questions=4, timeout=180):
    """
    Genera preguntas de evaluación y actividades prácticas basadas EXCLUSIVAMENTE
    en el texto provisto por el profesor. Cumple con la directriz de cero alucinaciones.
    """
    text = (material_text or '').strip()
    title = (material_title or 'Material Educativo').strip()
    requested_count = max(1, int(num_questions or 4))

    if not text:
        return {
            'success': False,
            'error': 'El material no contiene texto suficiente para generar actividades.',
            'questions': [],
            'activities': [],
            'source': 'error',
        }

    prompt = f'''Eres un evaluador pedagógico estricto para educación primaria ({grade}° grado).
Tu tarea es formular preguntas de comprensión y actividades basadas ÚNICA Y EXCLUSIVAMENTE en el siguiente texto del profesor.

TEXTO DEL PROFESOR:
"""
{text}
"""

REGLAS OBLIGATORIAS:
1. Las preguntas y opciones DEBEN derivarse directamente del texto del profesor.
2. NO agregues conceptos, nombres, fechas ni detalles que no figuren en el texto.
3. La respuesta correcta ("answer") DEBE copiar o parafrasear fielmente el contenido del texto.
4. Devuelve EXACTAMENTE {requested_count} preguntas distintas y ÚNICAMENTE un JSON válido con esta estructura exacta, sin markdown ni explicaciones:
{{
  "preguntas": [
    {{
      "question": "¿pregunta basada en el texto?",
      "options": ["opción correcta", "distractor 1", "distractor 2", "distractor 3"],
      "answer": "opción correcta",
      "reference_fragment": "oración exacta del texto que valida la respuesta"
    }}
  ],
  "actividades": [
    {{
      "title": "Actividad de {title}",
      "instruction": "instrucción guiada",
      "question": "¿pregunta de práctica?",
      "options": ["opción A", "opción B", "opción C"],
      "correct_answer": "opción A",
      "reference_fragment": "oración del texto"
    }}
  ]
}}
'''
    try:
        raw_response = _ollama_chat(prompt, timeout=timeout)
        parsed = _extract_json(raw_response)
        raw_questions = parsed.get('preguntas') or parsed.get('questions') or []
        raw_activities = parsed.get('actividades') or parsed.get('activities') or []

        def normalize(value):
            value = unicodedata.normalize('NFD', str(value or '').casefold())
            value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
            return re.sub(r'\s+', ' ', value).strip()

        source_normalized = normalize(text)
        normalized_questions = []
        seen_questions = set()
        for q in raw_questions:
            opts = [str(opt).strip() for opt in (q.get('options') or []) if str(opt).strip()]
            ans = str(q.get('answer') or q.get('correct_answer') or '').strip()
            q_text = str(q.get('question') or '').strip()
            reference = str(q.get('reference_fragment') or '').strip()
            answer_words = [word for word in re.findall(r'\w+', normalize(ans)) if len(word) >= 4]
            metadata_markers = ('prof:', 'tema:', 'temai:', 'computación', 'computacion')
            uses_metadata = (
                normalize(reference).startswith(metadata_markers)
                or normalize(q_text).startswith(metadata_markers)
                or normalize(ans).startswith(metadata_markers)
            )
            valid = (
                q_text
                and len(opts) >= 3
                and len(set(normalize(opt) for opt in opts)) == len(opts)
                and normalize(ans) in {normalize(opt) for opt in opts}
                and normalize(reference) in source_normalized
                and any(word in source_normalized for word in answer_words)
                and normalize(q_text) not in seen_questions
                and not uses_metadata
            )
            if valid:
                normalized_questions.append({
                    'question': q_text,
                    'options': opts,
                    'answer': ans,
                    'reference_fragment': reference,
                })
                seen_questions.add(normalize(q_text))

        normalized_activities = []
        for a in raw_activities:
            opts = a.get('options') or []
            ans = a.get('correct_answer') or a.get('answer') or ''
            if opts and ans:
                normalized_activities.append({
                    'title': a.get('title') or f'Actividad de {title}',
                    'instruction': a.get('instruction') or 'Responde según la lectura.',
                    'question': a.get('question', ''),
                    'options': opts,
                    'correct_answer': ans,
                    'reference_fragment': a.get('reference_fragment') or text[:80],
                })

        if len(normalized_questions) >= requested_count:
            print(f"[AI] modelo: {Config.AI_PROVIDER}")
            print(f"[AI] material: {title}")
            print(f"[AI] source: {Config.AI_PROVIDER}")
            return {
                'success': True,
                'source': Config.AI_PROVIDER,
                'material_title': title,
                'questions': normalized_questions,
                'activities': normalized_activities,
            }
    except Exception as exc:
        print(f"[AI] Ollama falló. reason: {exc}")

    # Fallback determinista fundamentado en el texto del docente
    fallback_q, fallback_a = _grounded_fallback_from_text(text, title, requested_count)
    print(f"[AI] modelo: {Config.AI_PROVIDER}")
    print(f"[AI] material: {title}")
    print("[AI] source: fallback")
    return {
        'success': True,
        'source': 'fallback',
        'material_title': title,
        'questions': fallback_q,
        'activities': fallback_a,
    }
