from __future__ import annotations

from typing import Any, Dict, List


def _question_bank(topic_title: str, grade: int) -> List[tuple[str, str, List[str]]]:
    title = topic_title.strip()
    lower_title = title.lower()
    if 'visual studio code' in lower_title or lower_title in {'vscode', 'vs code'}:
        return [
            (f'¿Para qué sirve el explorador de archivos de {title}?', 'Organizar y abrir los archivos del proyecto', ['Cambiar el volumen', 'Apagar la computadora', 'Crear una presentación']),
            (f'¿Qué permite hacer la terminal integrada de {title}?', 'Ejecutar comandos dentro del editor', ['Dibujar fotografías', 'Cambiar el teclado', 'Imprimir una hoja']),
            (f'¿Qué agrega una extensión a {title}?', 'Nuevas funciones al editor', ['Más batería', 'Un cable de red', 'Una carpeta física']),
            (f'¿Qué recurso ayuda a detectar errores en {title}?', 'Los mensajes del analizador y el resaltado', ['Cerrar el archivo', 'Borrar el proyecto', 'Cambiar el fondo']),
            (f'¿Qué permite hacer el depurador de {title}?', 'Revisar la ejecución paso a paso', ['Editar una foto', 'Crear música', 'Cambiar la hora']),
            (f'¿Por qué conviene guardar cambios en {title}?', 'Para conservar el trabajo antes de probarlo', ['Para apagar el monitor', 'Para borrar código', 'Para bloquear carpetas']),
            (f'¿Qué representa el resaltado de sintaxis en {title}?', 'Distingue palabras y elementos del código', ['Mide Internet', 'Cambia el idioma', 'Protege el teclado']),
            (f'¿Qué práctica es responsable al usar la terminal de {title}?', 'Revisar el comando antes de ejecutarlo', ['Compartir contraseñas', 'Abrir cualquier archivo', 'Borrar carpetas al azar']),
            (f'¿Qué se organiza dentro de un proyecto de {title}?', 'Carpetas, archivos y recursos relacionados', ['Solo imágenes', 'Únicamente sonidos', 'La pantalla del equipo']),
            (f'¿Qué acción ayuda a trabajar en equipo con {title}?', 'Nombrar archivos claramente y guardar cambios ordenados', ['Ocultar el código', 'Eliminar versiones', 'No guardar nunca']),
        ]
    if any(word in lower_title for word in ('word', 'paint', 'powerpoint', 'excel', 'computación', 'capcut')):
        return [
            (f'¿Qué herramienta de {title} permite crear o editar el contenido principal?', 'La herramienta de edición del programa', ['El botón de apagar', 'La papelera del sistema', 'El reloj de la computadora']),
            (f'¿Para qué sirve guardar un trabajo realizado en {title}?', 'Para conservarlo y poder abrirlo después', ['Para borrar el archivo', 'Para apagar el monitor', 'Para cambiar el teclado']),
            (f'¿Qué acción permite corregir un error mientras trabajas en {title}?', 'Usar Deshacer o corregir directamente el contenido', ['Cerrar el programa sin guardar', 'Desconectar la computadora', 'Imprimir una pantalla vacía']),
            (f'¿Qué elemento ayuda a organizar la información en un trabajo de {title}?', 'Títulos, imágenes y secciones ordenadas', ['Palabras al azar', 'Páginas sin contenido', 'Archivos duplicados']),
            (f'¿Por qué es importante revisar un trabajo antes de compartirlo desde {title}?', 'Para corregir errores y comprobar que el contenido sea claro', ['Para eliminarlo', 'Para cambiar la hora', 'Para evitar guardarlo']),
            (f'¿Qué formato conviene elegir al exportar un trabajo de {title}?', 'Un formato compatible con el uso que tendrá el archivo', ['Un formato que nadie pueda abrir', 'Un archivo vacío', 'Una carpeta temporal']),
            (f'¿Cómo se puede mejorar la presentación de un trabajo en {title}?', 'Aplicando formato y elementos relacionados con el tema', ['Quitando todo el texto', 'Usando colores sin orden', 'Repitiendo la misma imagen']),
            (f'¿Qué debes hacer para no perder un trabajo de {title}?', 'Guardar los cambios periódicamente', ['Apagar sin guardar', 'Borrar el documento', 'Cerrar todas las ventanas']),
            (f'¿Qué criterio ayuda a escoger una imagen para un trabajo de {title}?', 'Que sea pertinente y ayude a explicar el tema', ['Que no tenga relación', 'Que oculte el texto', 'Que esté dañada']),
            (f'¿Cuál es una práctica responsable al usar {title}?', 'Respetar la información y revisar el resultado antes de publicarlo', ['Copiar cualquier contenido', 'Compartir contraseñas', 'Eliminar el trabajo de otros']),
        ]
    if any(word in lower_title for word in ('fracción', 'decimal', 'matemática', 'suma', 'resta', 'multiplic')):
        return [
            (f'¿Qué representa una fracción relacionada con {title}?', 'Una cantidad dividida en partes iguales', ['Una fecha', 'Un color', 'Un sonido']),
            (f'¿Qué indica el denominador en un ejercicio de {title}?', 'En cuántas partes iguales se divide la unidad', ['El resultado final', 'El nombre del problema', 'La operación inversa']),
            (f'¿Qué indica el numerador al resolver {title}?', 'Cuántas partes se consideran', ['Cuántas unidades se borran', 'El tipo de figura', 'El nombre del estudiante']),
            (f'¿Qué paso conviene realizar primero en un problema de {title}?', 'Leer los datos y comprender lo que se pregunta', ['Adivinar el resultado', 'Cambiar los números', 'Copiar otra respuesta']),
            (f'¿Cómo se puede comprobar una respuesta de {title}?', 'Revisando la operación y comparando el resultado con el problema', ['Borrando el procedimiento', 'Ignorando las unidades', 'Usando un número al azar']),
            (f'¿Qué significa simplificar una expresión de {title}?', 'Escribirla de una forma equivalente y más sencilla', ['Cambiar su valor', 'Eliminar todos los números', 'Convertirla en una palabra']),
            (f'¿Qué estrategia ayuda a aprender {title}?', 'Representar el problema con dibujos o ejemplos', ['Evitar practicar', 'Memorizar sin comprender', 'No revisar los pasos']),
            (f'¿Cuándo dos cantidades de {title} son equivalentes?', 'Cuando representan el mismo valor', ['Cuando tienen colores distintos', 'Cuando aparecen en páginas diferentes', 'Cuando no se pueden comparar']),
            (f'¿Qué error debe evitarse al trabajar {title}?', 'Operar sin respetar los datos y el orden del procedimiento', ['Leer con atención', 'Escribir los pasos', 'Comprobar el resultado']),
            (f'¿Para qué sirve aprender {title}?', 'Para resolver situaciones numéricas de la vida diaria', ['Para eliminar problemas', 'Para evitar medir', 'Para cambiar las unidades sin razón']),
        ]
    return [
        (f'¿Cuál es la idea central de {title}?', f'Comprender {title} y aplicarlo correctamente', ['Ignorar el tema', 'Responder sin leer', 'Memorizar sin entender']),
        (f'¿Qué ejemplo ayuda a entender {title}?', f'Una situación cotidiana relacionada con {title}', ['Una situación sin relación', 'Una respuesta al azar', 'Un dato inventado']),
        (f'¿Qué debes identificar primero al estudiar {title}?', 'Los conceptos y datos principales', ['Los errores de otra persona', 'Una respuesta sin revisar', 'El final antes del inicio']),
        (f'¿Cómo se demuestra comprensión de {title}?', 'Explicando el procedimiento con un ejemplo', ['Repitiendo una palabra', 'Evitando preguntas', 'Copiando sin analizar']),
        (f'¿Qué recurso favorece el aprendizaje de {title}?', 'Una actividad práctica relacionada con el tema', ['Una instrucción incompleta', 'Un archivo vacío', 'Una respuesta desconectada']),
        (f'¿Qué ocurre al practicar {title} de forma constante?', 'Mejora la comprensión y se corrigen errores', ['Se pierde todo lo aprendido', 'No cambia nada', 'Se elimina el procedimiento']),
        (f'¿Qué afirmación es correcta sobre {title}?', f'{title} puede relacionarse con ejemplos reales', ['No tiene ninguna aplicación', 'Solo se aprende adivinando', 'No requiere comprensión']),
        (f'¿Qué estrategia ayuda a resolver una actividad de {title}?', 'Leer, resolver y revisar la respuesta', ['Responder sin leer', 'Omitir los datos', 'Cambiar la consigna']),
        (f'¿Por qué es útil relacionar {title} con la vida diaria?', 'Porque permite comprender su utilidad', ['Porque evita estudiar', 'Porque reemplaza todas las reglas', 'Porque elimina la práctica']),
        (f'¿Qué debes hacer al terminar una actividad sobre {title}?', 'Revisar el resultado y explicar la respuesta', ['Cerrar sin revisar', 'Borrar el trabajo', 'Dejar preguntas vacías']),
    ]


def build_evaluation_questions(topic_title: str, grade: int, existing: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    title = (topic_title or '').strip() or 'Tema nuevo'
    grade_value = int(grade) if grade else 5
    bank = _question_bank(title, grade_value)
    questions = []
    used_questions = set()
    for index, item in enumerate(list(existing or [])[:10]):
        question = dict(item)
        answer = question.get('answer', question.get('correct_answer', ''))
        question['id'] = question.get('id', index + 1)
        question['question'] = question.get('question', question.get('q', f'Pregunta sobre {title}'))
        legacy_question = (
            str(answer).lower().startswith('respuesta esperada')
            or str(question['question']).lower().startswith('explica con tus palabras')
            or str(question['question']).lower().startswith('¿qué ejercicio te ayuda mejor')
        )
        if legacy_question:
            continue
        question_key = question['question'].strip().lower()
        if question_key in used_questions:
            continue
        used_questions.add(question_key)
        question['answer'] = answer
        question['options'] = question.get('options') or [
            answer,
            'Ignorar el tema',
            'Responder sin revisar',
            'Ninguna de las anteriores',
        ]
        questions.append(question)
    while len(questions) < 10:
        index = len(questions)
        question, answer, distractors = bank[index % len(bank)]
        if question.lower() in used_questions:
            continue
        used_questions.add(question.lower())
        answer_index = (sum(ord(char) for char in title) + index) % 4
        options = [answer] + distractors
        options[0], options[answer_index] = options[answer_index], options[0]
        questions.append({
            'id': index + 1,
            'question': question,
            'options': options,
            'answer': answer,
            'difficulty': 'media',
            'score': 2,
        })
    return questions


def build_topic_generation_payload(topic_title: str, grade: int) -> Dict[str, Any]:
    title = (topic_title or '').strip() or 'Tema nuevo'
    grade_value = int(grade) if grade else 5
    curriculum_plan = (
        f"**Grado:** {grade_value}° Grado\n"
        f"**Asignatura / Tema:** {title}\n\n"
        "# Planificación educativa completa\n\n"
        "## 📅 BIMESTRE I\n"
        "- **📂 Unidad 1 (Sesiones 1 a 4):** Introducción y descubrimiento de la temática\n"
        "  - **Sesión 1:** Introducción a la temática — **Objetivo:** reconocer los conceptos básicos del tema.\n"
        "  - **Sesión 2:** Conceptos clave — **Objetivo:** comprender las ideas principales mediante ejemplos sencillos.\n"
        "  - **Sesión 3:** Práctica guiada — **Objetivo:** poner en acción lo aprendido con ejercicios básicos.\n"
        "  - **Sesión 4:** Revisión y cierre — **Objetivo:** consolidar lo trabajado y verificar avances.\n"
        "- **📂 Unidad 2 (Sesiones 5 a 8):** Conceptos fundamentales y práctica guiada\n"
        "  - **Sesión 5:** Repaso y conexión — **Objetivo:** reforzar conceptos previos y relacionarlos con el tema.\n"
        "  - **Sesión 6:** Aplicación práctica — **Objetivo:** resolver actividades sencillas con apoyo docente.\n"
        "  - **Sesión 7:** Ejercicios de comprensión — **Objetivo:** desarrollar claridad conceptual y análisis.\n"
        "  - **Sesión 8:** Evaluación breve — **Objetivo:** comprobar el avance del aprendizaje.\n\n"
        "## 📅 BIMESTRE II\n"
        "- **📂 Unidad 3 (Sesiones 9 a 12):** Aplicación en situaciones reales\n"
        "  - **Sesión 9:** Contextos reales — **Objetivo:** relacionar el tema con ejemplos cotidianos.\n"
        "  - **Sesión 10:** Observación y análisis — **Objetivo:** identificar elementos relevantes de la temática.\n"
        "  - **Sesión 11:** Actividades contextualizadas — **Objetivo:** aplicar conocimientos en situaciones concretas.\n"
        "  - **Sesión 12:** Revisión y mejora — **Objetivo:** corregir errores y fortalecer la comprensión.\n"
        "- **📂 Unidad 4 (Sesiones 13 a 16):** Proyecto inicial y consolidación\n"
        "  - **Sesión 13:** Planteamiento del proyecto — **Objetivo:** definir metas y pasos para resolver una tarea.\n"
        "  - **Sesión 14:** Desarrollo del proyecto — **Objetivo:** poner en práctica lo aprendido con apoyo.\n"
        "  - **Sesión 15:** Retroalimentación — **Objetivo:** revisar avances y mejorar resultados.\n"
        "  - **Sesión 16:** Cierre de proyecto — **Objetivo:** presentar y valorar el aprendizaje logrado.\n\n"
        "## 📅 BIMESTRE III\n"
        "- **📂 Unidad 5 (Sesiones 17 a 20):** Profundización y análisis\n"
        "  - **Sesión 17:** Exploración profunda — **Objetivo:** ampliar conceptos y ampliar ejemplos.\n"
        "  - **Sesión 18:** Análisis del contenido — **Objetivo:** distinguir ideas principales y secundarias.\n"
        "  - **Sesión 19:** Trabajo colaborativo — **Objetivo:** intercambiar ideas y fortalecer el razonamiento.\n"
        "  - **Sesión 20:** Revisión y práctica — **Objetivo:** sintetizar contenidos y reforzar habilidades.\n"
        "- **📂 Unidad 6 (Sesiones 21 a 24):** Resolución de problemas\n"
        "  - **Sesión 21:** Identificación del problema — **Objetivo:** entender la situación a resolver.\n"
        "  - **Sesión 22:** Estrategias de solución — **Objetivo:** seleccionar procedimientos adecuados.\n"
        "  - **Sesión 23:** Ejercicios de aplicación — **Objetivo:** practicar soluciones y verificar respuestas.\n"
        "  - **Sesión 24:** Evaluación formativa — **Objetivo:** evaluar el progreso del aprendizaje.\n\n"
        "## 📅 BIMESTRE IV\n"
        "- **📂 Unidad 7 (Sesiones 25 a 28):** Producción creativa y evaluación\n"
        "  - **Sesión 25:** Diseño y creatividad — **Objetivo:** crear propuestas originales relacionadas con el tema.\n"
        "  - **Sesión 26:** Producción de trabajos — **Objetivo:** organizar ideas y material de trabajo.\n"
        "  - **Sesión 27:** Presentación y socialización — **Objetivo:** comunicar aprendizajes con claridad.\n"
        "  - **Sesión 28:** Retroalimentación final — **Objetivo:** mejorar resultados y evidenciar avance.\n"
        "- **📂 Unidad 8 (Sesiones 29 a 32):** Cierre, transferencia y reflexión\n"
        "  - **Sesión 29:** Síntesis del tema — **Objetivo:** resumir ideas clave y relaciones principales.\n"
        "  - **Sesión 30:** Transferencia a contextos nuevos — **Objetivo:** aplicar conocimientos en situaciones distintas.\n"
        "  - **Sesión 31:** Proyecto final — **Objetivo:** integrar todo el aprendizaje en una tarea final.\n"
        "  - **Sesión 32:** Evaluación final y cierre — **Objetivo:** demostrar dominio del tema y reflexionar sobre el proceso.\n"
    )
    explanation = (
        f"{title} es un tema clave para {grade_value}° grado. El objetivo es comprender su uso práctico, identificar ejemplos cotidianos y aplicar la idea en actividades sencillas a lo largo de cuatro bimestres con 32 sesiones correlativas."
    )
    examples = [
        f"Ejemplo 1: explica {title} con un caso cotidiano del aula.",
        f"Ejemplo 2: relaciona {title} con una situación de la vida diaria.",
        f"Ejemplo 3: muestra cómo resolver un problema usando {title}.",
    ]
    activities = [
        {
            'type': 'selección múltiple',
            'question': f'¿Cuál es la idea principal de {title}?',
            'options': ['a) Aplicarlo en la práctica', 'b) Ignorarlo', 'c) Memorizar sin entender', 'd) Evitar su uso'],
            'correct_answer': 'a) Aplicarlo en la práctica',
            'score': 5,
        },
        {
            'type': 'verdadero/falso',
            'question': f'{title} ayuda a reforzar el aprendizaje práctico.',
            'correct_answer': 'Verdadero',
            'score': 5,
        },
    ]
    evaluation_questions = build_evaluation_questions(title, grade_value)
    game = {
        'name': f'Juego de {title}',
        'description': f'Una actividad lúdica para reforzar {title} con retos cortos y retroalimentación inmediata.',
        'rules': ['Lee la consigna', 'Responde correctamente', 'Gana puntos por cada acierto'],
        'active': True,
    }
    description = (
        f"{title} es un tema clave para {grade_value}° grado. "
        f"Se trabaja con actividades prácticas, ejemplos cotidianos y evaluación gradual para comprenderlo y aplicarlo con confianza."
    )
    payload = {
        'title': title,
        'description': description,
        'grade': grade_value,
        'explanation': explanation,
        'examples': examples,
        'activities': activities,
        'evaluation_questions': evaluation_questions,
        'game': game,
        'feedback': f'Se recomienda reforzar {title} con práctica breve y revisión de ejemplos para consolidar el aprendizaje.',
        'status': 'En proceso',
    }
    return payload


def build_teacher_dashboard_summary(
    students: List[Dict[str, Any]],
    topics: List[Dict[str, Any]],
    activities_count: int = 0,
    evaluations_count: int = 0,
    alerts: List[str] | None = None,
) -> Dict[str, Any]:
    total_students = len(students or [])
    students_by_grade: Dict[str, int] = {}
    progress_values: List[int] = []
    for student in students or []:
        grade = student.get('grade', 0)
        grade_label = f'{grade}°'
        students_by_grade[grade_label] = students_by_grade.get(grade_label, 0) + 1
        progress = student.get('progress', 0)
        try:
            progress_values.append(int(progress))
        except (TypeError, ValueError):
            continue

    average_progress = round(sum(progress_values) / len(progress_values)) if progress_values else 0
    available_topics = len(topics or [])
    low_performance_students = [
        f"{student.get('first_name', 'Estudiante')} {student.get('last_name', '')}".strip()
        for student in students or []
        if int(student.get('progress', 0)) < 50
    ]

    performance_by_grade: Dict[str, int] = {}
    for student in students or []:
        grade_label = f"{student.get('grade', 0)}°"
        performance_by_grade.setdefault(grade_label, 0)
        performance_by_grade[grade_label] = int(performance_by_grade[grade_label]) + int(student.get('progress', 0))

    normalized_performance: Dict[str, int] = {}
    for grade_label, total in performance_by_grade.items():
        count = students_by_grade.get(grade_label, 0)
        normalized_performance[grade_label] = round(total / count) if count else 0

    return {
        'total_students': total_students,
        'students_by_grade': students_by_grade,
        'average_progress': average_progress,
        'activities_count': int(activities_count),
        'evaluations_count': int(evaluations_count),
        'available_topics': available_topics,
        'low_performance_students': low_performance_students,
        'performance_by_grade': normalized_performance,
        'alerts': alerts or [
            'Se recomienda reforzar lectura comprensiva en 4° grado.',
            'Hay 2 estudiantes con riesgo de bajo rendimiento en matemáticas.',
        ],
    }
