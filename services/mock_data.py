MOCK_TOPICS = {
    4: [
        {'id': 1, 'title': 'Sumas y restas', 'description': 'Operaciones básicas con números hasta 1000.', 'status': 'Publicado', 'grade': 4},
        {'id': 2, 'title': 'Lectura comprensiva', 'description': 'Comprensión de textos cortos con preguntas.', 'status': 'Publicado', 'grade': 4},
        {'id': 3, 'title': 'Ecosistemas', 'description': 'Conoce los ecosistemas de tu región.', 'status': 'Publicado', 'grade': 4},
    ],
    5: [
        {'id': 4, 'title': 'Fracciones básicas', 'description': 'Introducción a las fracciones y ejercicios básicos.', 'status': 'Publicado', 'grade': 5},
        {'id': 5, 'title': 'Lectura comprensiva', 'description': 'Comprensión de textos con inferencias.', 'status': 'Publicado', 'grade': 5},
        {'id': 6, 'title': 'Cuerpo humano', 'description': 'Sistemas del cuerpo humano y su función.', 'status': 'Publicado', 'grade': 5},
    ],
    6: [
        {'id': 7, 'title': 'Fracciones y decimales', 'description': 'Operaciones con fracciones y decimales.', 'status': 'Publicado', 'grade': 6},
        {'id': 8, 'title': 'Geometría básica', 'description': 'Figuras geométricas, perímetro y área.', 'status': 'Publicado', 'grade': 6},
        {'id': 9, 'title': 'Historia de México', 'description': 'Independencia y reforma.', 'status': 'Publicado', 'grade': 6},
    ],
}

MOCK_STUDENTS = [
    {'id': 1, 'first_name': 'Juan', 'last_name': 'Demo', 'grade': 5, 'section': 'A', 'progress': 35},
    {'id': 2, 'first_name': 'Maria', 'last_name': 'Demo', 'grade': 5, 'section': 'A', 'progress': 45},
    {'id': 3, 'first_name': 'Pedro', 'last_name': 'Demo', 'grade': 4, 'section': 'A', 'progress': 65},
    {'id': 4, 'first_name': 'Ana', 'last_name': 'Demo', 'grade': 6, 'section': 'A', 'progress': 80},
]

MOCK_USERS = {
    'profesor1': {'id': 1, 'role': 'teacher', 'first_name': 'Docente', 'last_name': 'Demo', 'password_hash': 'Admin123'},
    'alumno1': {'id': 2, 'role': 'student', 'first_name': 'Juan', 'last_name': 'Demo', 'grade': 5, 'section': 'A', 'student_id': 1, 'password_hash': 'Alumno123'},
}

MOCK_PROGRESS = {
    1: {'overall_progress': 35, 'completed_topics': 2, 'study_time': '2h 15m', 'average_grade': 78},
    2: {'overall_progress': 45, 'completed_topics': 3, 'study_time': '3h 10m', 'average_grade': 85},
    3: {'overall_progress': 65, 'completed_topics': 4, 'study_time': '4h 00m', 'average_grade': 88},
    4: {'overall_progress': 80, 'completed_topics': 5, 'study_time': '5h 00m', 'average_grade': 90},
}

MOCK_RECOMMENDATIONS = [
    {'title': 'Reforzar fracciones', 'summary': 'Repasa el tema "Fracciones básicas" con actividades interactivas.'},
    {'title': 'Juego recomendado', 'summary': 'Practica con Memorama de operaciones matemáticas.'},
    {'title': 'Siguiente tema', 'summary': 'Cuando completes fracciones, avanza a "Cuerpo humano".'},
]

MOCK_MESSAGES = {
    1: [
        {'id': 1, 'message': 'Recuerda repasar fracciones antes de la próxima clase.', 'is_read': False, 'created_at': '2024-01-20T09:00:00'},
        {'id': 2, 'message': 'Muy buen trabajo en la tarea de lectura.', 'is_read': True, 'created_at': '2024-01-18T10:15:00'},
    ],
    2: [
        {'id': 3, 'message': 'Tu progreso en matemáticas va muy bien.', 'is_read': False, 'created_at': '2024-01-19T11:30:00'},
    ],
    3: [
        {'id': 4, 'message': 'Hoy reforzaremos ecosistemas en clase.', 'is_read': True, 'created_at': '2024-01-17T08:45:00'},
    ],
    4: [
        {'id': 5, 'message': 'Excelente participación en geografía.', 'is_read': False, 'created_at': '2024-01-16T12:20:00'},
    ],
}

MOCK_SUBMISSIONS = []

MOCK_ALERTS = [
    {'id': 1, 'alert_type': 'warning', 'title': 'Riesgo académico', 'description': 'Juan está por debajo del nivel esperado en lectura.', 'is_read': False, 'created_at': '2024-01-22T08:00:00'},
    {'id': 2, 'alert_type': 'info', 'title': 'Tarea enviada', 'description': 'María entregó la tarea de fracciones a tiempo.', 'is_read': True, 'created_at': '2024-01-21T09:15:00'},
    {'id': 3, 'alert_type': 'success', 'title': 'Meta alcanzada', 'description': 'Carlos superó su objetivo semanal de ejercicios.', 'is_read': False, 'created_at': '2024-01-20T11:00:00'},
]

MOCK_STUDENT_NOTES = [
    # Juan Pérez (Estudiante 1 - 5° Grado: Perfil de Riesgo Alto)
    {'id': 1, 'student_id': 1, 'student_name': 'Juan Pérez', 'topic_id': 4, 'topic': 'Fracciones básicas', 'activity_type': 'evaluaciones', 'score': 7.0, 'percentage': 35.0, 'correct_answers': 3, 'wrong_answers': 7, 'time_spent_seconds': 320, 'created_at': '2024-03-10T10:00:00'},
    {'id': 2, 'student_id': 1, 'student_name': 'Juan Pérez', 'topic_id': 4, 'topic': 'Fracciones básicas', 'activity_type': 'actividades', 'score': 8.0, 'percentage': 40.0, 'correct_answers': 4, 'wrong_answers': 6, 'time_spent_seconds': 280, 'created_at': '2024-03-18T11:00:00'},
    {'id': 3, 'student_id': 1, 'student_name': 'Juan Pérez', 'topic_id': 5, 'topic': 'Lectura comprensiva', 'activity_type': 'evaluaciones', 'score': 5.0, 'percentage': 25.0, 'correct_answers': 2, 'wrong_answers': 8, 'time_spent_seconds': 400, 'created_at': '2024-03-25T09:30:00'},

    # María García (Estudiante 2 - 5° Grado: Perfil de Riesgo Moderado / Medio)
    {'id': 4, 'student_id': 2, 'student_name': 'María García', 'topic_id': 4, 'topic': 'Fracciones básicas', 'activity_type': 'evaluaciones', 'score': 9.5, 'percentage': 47.5, 'correct_answers': 5, 'wrong_answers': 5, 'time_spent_seconds': 240, 'created_at': '2024-03-10T10:00:00'},
    {'id': 5, 'student_id': 2, 'student_name': 'María García', 'topic_id': 4, 'topic': 'Fracciones básicas', 'activity_type': 'actividades', 'score': 10.5, 'percentage': 52.5, 'correct_answers': 5, 'wrong_answers': 5, 'time_spent_seconds': 220, 'created_at': '2024-03-18T11:00:00'},
    {'id': 6, 'student_id': 2, 'student_name': 'María García', 'topic_id': 5, 'topic': 'Lectura comprensiva', 'activity_type': 'evaluaciones', 'score': 10.0, 'percentage': 50.0, 'correct_answers': 5, 'wrong_answers': 5, 'time_spent_seconds': 250, 'created_at': '2024-03-25T09:30:00'},

    # Carlos López (Estudiante 3 - 4° Grado: Perfil Regular / Bajo Riesgo)
    {'id': 7, 'student_id': 3, 'student_name': 'Carlos López', 'topic_id': 1, 'topic': 'Sumas y restas', 'activity_type': 'evaluaciones', 'score': 14.0, 'percentage': 70.0, 'correct_answers': 7, 'wrong_answers': 3, 'time_spent_seconds': 190, 'created_at': '2024-03-10T10:00:00'},
    {'id': 8, 'student_id': 3, 'student_name': 'Carlos López', 'topic_id': 1, 'topic': 'Sumas y restas', 'activity_type': 'actividades', 'score': 15.0, 'percentage': 75.0, 'correct_answers': 8, 'wrong_answers': 2, 'time_spent_seconds': 180, 'created_at': '2024-03-18T11:00:00'},
    {'id': 9, 'student_id': 3, 'student_name': 'Carlos López', 'topic_id': 2, 'topic': 'Lectura comprensiva', 'activity_type': 'evaluaciones', 'score': 14.5, 'percentage': 72.5, 'correct_answers': 7, 'wrong_answers': 3, 'time_spent_seconds': 210, 'created_at': '2024-03-25T09:30:00'},

    # Ana Martínez (Estudiante 4 - 6° Grado: Perfil Destacado / Bajo Riesgo)
    {'id': 10, 'student_id': 4, 'student_name': 'Ana Martínez', 'topic_id': 7, 'topic': 'Fracciones y decimales', 'activity_type': 'evaluaciones', 'score': 18.0, 'percentage': 90.0, 'correct_answers': 9, 'wrong_answers': 1, 'time_spent_seconds': 150, 'created_at': '2024-03-10T10:00:00'},
    {'id': 11, 'student_id': 4, 'student_name': 'Ana Martínez', 'topic_id': 7, 'topic': 'Fracciones y decimales', 'activity_type': 'actividades', 'score': 18.5, 'percentage': 92.5, 'correct_answers': 9, 'wrong_answers': 1, 'time_spent_seconds': 140, 'created_at': '2024-03-18T11:00:00'},
    {'id': 12, 'student_id': 4, 'student_name': 'Ana Martínez', 'topic_id': 8, 'topic': 'Geometría básica', 'activity_type': 'evaluaciones', 'score': 19.0, 'percentage': 95.0, 'correct_answers': 10, 'wrong_answers': 0, 'time_spent_seconds': 130, 'created_at': '2024-03-25T09:30:00'},
]

MOCK_MATERIALS = [
    {
        'id': 1, 'topic_id': 4, 'title': 'Guía de fracciones básicas', 'material_type': 'texto',
        'description': 'Explicación paso a paso de las fracciones.',
        'content': 'Una fracción representa las partes iguales en las que se divide un todo o unidad. El numerador indica cuántas partes tomamos y el denominador indica el total de partes.',
        'resource_url': '',
    },
    {
        'id': 2, 'topic_id': 4, 'title': 'Presentación de operaciones', 'material_type': 'presentacion',
        'description': 'Material de apoyo de la sesión.', 'content': '',
        'resource_url': '/static/uploads/presentations/introduccion_fracciones.pptx',
    },
    {
        'id': 3, 'topic_id': 5, 'title': 'Fotosíntesis', 'material_type': 'texto',
        'description': 'Lectura explicativa sobre cómo las plantas producen su energía.',
        'content': 'Las plantas producen energía mediante el proceso de la fotosíntesis utilizando luz solar, agua y dióxido de carbono. La clorofila es el pigmento verde presente en las hojas encargado de absorber la luz del sol. Mediante este proceso natural, las plantas fabrican glucosa para nutrirse y expulsan oxígeno al medio ambiente, el cual es vital para los seres humanos.',
        'resource_url': '',
    },
    {
        'id': 4, 'topic_id': 1, 'title': 'Partes de la computadora', 'material_type': 'texto',
        'description': 'Hardware principal y periféricos.',
        'content': 'La computadora se compone de monitor, teclado, mouse y CPU. El teclado permite escribir y el monitor ver los datos.',
        'resource_url': '',
    },
]

MOCK_PRESENTATIONS = [
    {
        'id': 1,
        'topic_id': 4,
        'title': 'Presentación: Introducción a las Fracciones',
        'description': 'Diapositivas de la sesión de fracciones',
        'session_number': 1,
        'file_path': '/static/uploads/presentations/introduccion_fracciones.pptx',
        'file_name': 'introduccion_fracciones.pptx',
        'file_size': 10240,
        'uploaded_by': 1,
    },
    {
        'id': 2,
        'topic_id': 6,
        'title': 'Presentación: El Cuerpo Humano y los Sistemas',
        'description': 'Diapositivas sobre los sistemas respiratorio y circulatorio',
        'session_number': 2,
        'file_path': '/static/uploads/presentations/cuerpo_humano.pptx',
        'file_name': 'cuerpo_humano.pptx',
        'file_size': 12400,
        'uploaded_by': 1,
    },
]

MOCK_TOPIC_ITEMS = {}
MOCK_ACADEMIC_OUTCOMES = []

MOCK_ASSESSMENTS = [
    {
        'id': 1,
        'topic_id': 4,
        'teacher_id': 1,
        'title': 'Evaluación de Fracciones Básicas',
        'status': 'PUBLISHED',
        'created_at': '2024-03-01T10:00:00',
    },
    {
        'id': 2,
        'topic_id': 5,
        'teacher_id': 1,
        'title': 'Evaluación de Fotosíntesis',
        'status': 'PENDING_REVIEW',
        'created_at': '2024-03-05T11:00:00',
    },
]

MOCK_ASSESSMENT_ATTEMPTS = []

MOCK_ASSESSMENT_QUESTIONS = [
    {
        'id': 1,
        'assessment_id': 1,
        'question': '¿Qué indica el numerador en una fracción?',
        'option_a': 'Las partes que se toman de la unidad',
        'option_b': 'El total de partes en que se dividió',
        'option_c': 'El color de la figura geométrica',
        'answer': 'Las partes que se toman de la unidad',
        'subtopic': 'Conceptos de fracciones',
        'approved': True,
        'created_at': '2024-03-01T10:05:00',
    },
    {
        'id': 2,
        'assessment_id': 1,
        'question': '¿Qué indica el denominador en una fracción?',
        'option_a': 'El total de partes iguales en que se divide el todo',
        'option_b': 'La suma de todos los números',
        'option_c': 'El resultado de una multiplicación',
        'answer': 'El total de partes iguales en que se divide el todo',
        'subtopic': 'Conceptos de fracciones',
        'approved': True,
        'created_at': '2024-03-01T10:06:00',
    },
    {
        'id': 3,
        'assessment_id': 1,
        'question': '¿Qué es una fracción propia?',
        'option_a': 'Aquella donde el numerador es menor que el denominador',
        'option_b': 'Aquella donde el numerador es mayor que el denominador',
        'option_c': 'Una fracción que no tiene números',
        'answer': 'Aquella donde el numerador es menor que el denominador',
        'subtopic': 'Tipos de fracciones',
        'approved': True,
        'created_at': '2024-03-01T10:07:00',
    },
    {
        'id': 4,
        'assessment_id': 1,
        'question': '¿Cuál es el resultado de sumar 2/7 + 3/7?',
        'option_a': '5/7',
        'option_b': '5/14',
        'option_c': '6/7',
        'answer': '5/7',
        'subtopic': 'Suma de fracciones',
        'approved': True,
        'created_at': '2024-03-01T10:08:00',
    },
    {
        'id': 5,
        'assessment_id': 1,
        'question': '¿Cuál es el resultado de restar 8/9 - 3/9?',
        'option_a': '5/9',
        'option_b': '5/0',
        'option_c': '11/9',
        'answer': '5/9',
        'subtopic': 'Resta de fracciones',
        'approved': True,
        'created_at': '2024-03-01T10:09:00',
    },
    {
        'id': 6,
        'assessment_id': 1,
        'question': '¿Cómo se multiplican dos fracciones como 2/3 x 4/5?',
        'option_a': 'Se multiplican numeradores entre sí y denominadores entre sí (8/15)',
        'option_b': 'Se multiplican en cruz y se suman',
        'option_c': 'Se suman los denominadores directamente',
        'answer': 'Se multiplican numeradores entre sí y denominadores entre sí (8/15)',
        'subtopic': 'Multiplicación',
        'approved': True,
        'created_at': '2024-03-01T10:10:00',
    },
    {
        'id': 7,
        'assessment_id': 1,
        'question': '¿Cuánto es el producto de 3 x 2/5?',
        'option_a': '6/5',
        'option_b': '6/15',
        'option_c': '5/6',
        'answer': '6/5',
        'subtopic': 'Multiplicación',
        'approved': True,
        'created_at': '2024-03-01T10:11:00',
    },
    {
        'id': 8,
        'assessment_id': 1,
        'question': '¿Cómo se divide una fracción entre otra como (3/4) ÷ (2/5)?',
        'option_a': 'Multiplicando la primera fracción por la inversa de la segunda (3/4 x 5/2 = 15/8)',
        'option_b': 'Restando los numeradores y sumando denominadores',
        'option_c': 'Dividiendo solo los numeradores',
        'answer': 'Multiplicando la primera fracción por la inversa de la segunda (3/4 x 5/2 = 15/8)',
        'subtopic': 'División',
        'approved': True,
        'created_at': '2024-03-01T10:12:00',
    },
    {
        'id': 9,
        'assessment_id': 1,
        'question': '¿Cuál es el resultado de resolver (1/2) ÷ (1/4)?',
        'option_a': '2',
        'option_b': '1/8',
        'option_c': '1/2',
        'answer': '2',
        'subtopic': 'División',
        'approved': True,
        'created_at': '2024-03-01T10:13:00',
    },
    {
        'id': 10,
        'assessment_id': 1,
        'question': '¿Qué significa simplificar la fracción 6/8?',
        'option_a': 'Dividir numerador y denominador por 2 para obtener 3/4',
        'option_b': 'Restar 2 a ambos términos',
        'option_c': 'Multiplicar por 10',
        'answer': 'Dividir numerador y denominador por 2 para obtener 3/4',
        'subtopic': 'Simplificación',
        'approved': True,
        'created_at': '2024-03-01T10:14:00',
    },
    {
        'id': 11,
        'assessment_id': 1,
        'question': '¿Cuál de las siguientes fracciones es equivalente a 1/3?',
        'option_a': '3/9',
        'option_b': '2/5',
        'option_c': '3/6',
        'answer': '3/9',
        'subtopic': 'Equivalencia',
        'approved': True,
        'created_at': '2024-03-01T10:15:00',
    },
    {
        'id': 12,
        'assessment_id': 1,
        'question': 'Al comparar 3/5 y 4/5, ¿cuál afirmación es correcta?',
        'option_a': '4/5 es mayor porque tiene igual denominador y mayor numerador',
        'option_b': '3/5 es mayor porque 3 es impar',
        'option_c': 'Son exactamente iguales',
        'answer': '4/5 es mayor porque tiene igual denominador y mayor numerador',
        'subtopic': 'Comparación',
        'approved': True,
        'created_at': '2024-03-01T10:16:00',
    },
    {
        'id': 13,
        'assessment_id': 1,
        'question': 'Si una receta pide 1/4 kg de azúcar por porción, ¿cuánto se necesita para 6 porciones?',
        'option_a': '6/4 kg (o 1 kg y medio)',
        'option_b': '1/24 kg',
        'option_c': '7/4 kg',
        'answer': '6/4 kg (o 1 kg y medio)',
        'subtopic': 'Multiplicación',
        'approved': True,
        'created_at': '2024-03-01T10:17:00',
    },
    {
        'id': 14,
        'assessment_id': 1,
        'question': 'Si repartimos 3/4 de pizza en porciones de 1/8 cada una, ¿cuántas porciones obtenemos?',
        'option_a': '6 porciones',
        'option_b': '3 porciones',
        'option_c': '24 porciones',
        'answer': '6 porciones',
        'subtopic': 'División',
        'approved': True,
        'created_at': '2024-03-01T10:18:00',
    },
    {
        'id': 15,
        'assessment_id': 1,
        'question': '¿Cómo se expresa la fracción impropia 7/3 como número mixto?',
        'option_a': '2 enteros y 1/3',
        'option_b': '3 enteros y 1/7',
        'option_c': '1 entero y 4/3',
        'answer': '2 enteros y 1/3',
        'subtopic': 'Números mixtos',
        'approved': True,
        'created_at': '2024-03-01T10:19:00',
    },
    {
        'id': 16,
        'assessment_id': 2,
        'question': '¿Qué pigmento verde absorbe la luz solar durante la fotosíntesis?',
        'option_a': 'Clorofila',
        'option_b': 'Hemoglobina',
        'option_c': 'Melanina',
        'answer': 'Clorofila',
        'subtopic': 'Pigmentos',
        'approved': False,
        'created_at': '2024-03-05T11:05:00',
    },
    {
        'id': 17,
        'assessment_id': 2,
        'question': '¿Qué gas expulsan las plantas hacia el medio ambiente durante la fotosíntesis?',
        'option_a': 'Oxígeno',
        'option_b': 'Monóxido de carbono',
        'option_c': 'Helio',
        'answer': 'Oxígeno',
        'subtopic': 'Gases',
        'approved': False,
        'created_at': '2024-03-05T11:06:00',
    },
]

MOCK_GAME_ATTEMPTS = []

MOCK_REINFORCEMENT_GAMES = [
    {
        'id': 1,
        'title': 'Juego 1: Multiplicación Rápida',
        'game_type': 'opcion_multiple',
        'topic_id': 4,
        'topic_title': 'Multiplicación y Operaciones',
        'grade': 5,
        'question': '¿Cuánto es 5x5?',
        'options': ['20', '25', '30'],
        'correct_answer': '25',
        'feedback_correct': '¡Excelente! 5x5 = 25. Has dominado esta multiplicación.',
        'feedback_incorrect': '5 multiplicado por 5 es 25 (5 + 5 + 5 + 5 + 5 = 25).',
        'weakness_keywords': ['multiplicación', 'multiplicar', 'producto', 'multiplicaciones', 'tablas', 'cálculo'],
        'instructions': 'Selecciona la alternativa correcta para responder la operación.',
    },
    {
        'id': 2,
        'title': 'Juego 2: Reto del Sistema Solar',
        'game_type': 'verdadero_falso',
        'topic_id': 6,
        'topic_title': 'El Sistema Solar y la Tierra',
        'grade': 5,
        'question': 'La tierra gira alrededor del sol.',
        'options': ['Verdadero', 'Falso'],
        'correct_answer': 'Verdadero',
        'feedback_correct': '¡Correcto! La Tierra realiza un movimiento de traslación alrededor del Sol que dura 365 días.',
        'feedback_incorrect': 'La afirmación es Verdadera: la Tierra gira en órbita alrededor del Sol.',
        'weakness_keywords': ['tierra', 'sol', 'sistema solar', 'universo', 'planetas', 'ciencias', 'astronomía'],
        'instructions': 'Determina si la afirmación es Verdadera o Falsa.',
    },
    {
        'id': 3,
        'title': 'Juego 3: Naturaleza y Plantas',
        'game_type': 'completar',
        'topic_id': 5,
        'topic_title': 'Fotosíntesis y Ciencias Naturales',
        'grade': 5,
        'question': 'La fotosíntesis ocurre en ______',
        'options': ['las hojas', 'las raíces', 'las piedras'],
        'correct_answer': 'las hojas',
        'acceptable_answers': ['las hojas', 'hojas', 'los cloroplastos', 'cloroplastos'],
        'feedback_correct': '¡Muy bien! La fotosíntesis se produce en las hojas gracias a los cloroplastos y la clorofila.',
        'feedback_incorrect': 'La fotosíntesis ocurre en las hojas de las plantas, capturando luz solar para elaborar alimento.',
        'weakness_keywords': ['fotosíntesis', 'plantas', 'hojas', 'clorofila', 'cloroplastos', 'ciencias naturales'],
        'instructions': 'Elige la palabra del banco o escríbela para completar la oración.',
    }
]

MOCK_AI_GENERATED_GAMES = [
    {
        'id': 1,
        'topic_id': 4,
        'material_id': None,
        'presentation_id': 1,
        'game_type': 'multiple_choice',
        'title': 'El Viaje de las Fracciones',
        'instruction': 'Selecciona la respuesta correcta para avanzar en la aventura.',
        'content_json': {
            'question': '¿Qué representa el número superior en una fracción (numerador)?',
            'options': ['Las partes que tomamos', 'El total de partes iguales', 'Un número al azar'],
            'answer': 'Las partes que tomamos',
            'explanation': 'El numerador indica cuántas partes tomamos o consideramos de la unidad.',
        },
        'status': 'PUBLISHED',
        'created_by': 1,
        'created_at': '2026-09-18T10:00:00',
    },
    {
        'id': 2,
        'topic_id': 6,
        'material_id': None,
        'presentation_id': 2,
        'game_type': 'true_false',
        'title': 'Verdades del Sistema Respiratorio',
        'instruction': 'Indica si la afirmación es verdadera o falsa.',
        'content_json': {
            'statement': 'Los pulmones absorben oxígeno del aire y expulsan dióxido de carbono.',
            'correct_answer': True,
            'explanation': 'La respiración permite intercambiar oxígeno por dióxido de carbono en los alvéolos.',
        },
        'status': 'PUBLISHED',
        'created_by': 1,
        'created_at': '2026-09-18T11:00:00',
    },
    {
        'id': 3,
        'topic_id': 5,
        'material_id': 1,
        'presentation_id': None,
        'game_type': 'fill_blank',
        'title': 'La Clorofila Mágica',
        'instruction': 'Completa la oración seleccionando la palabra correcta.',
        'content_json': {
            'sentence': 'La fotosíntesis ocurre en las ______ de las plantas con ayuda de la luz solar.',
            'blank_word': 'hojas',
            'options': ['hojas', 'flores', 'raíces'],
            'answers': ['hojas'],
            'explanation': 'Las hojas contienen clorofila para capturar la energía del sol.',
        },
        'status': 'PUBLISHED',
        'created_by': 1,
        'created_at': '2026-09-18T12:00:00',
    },
    {
        'id': 4,
        'topic_id': 4,
        'material_id': None,
        'presentation_id': 1,
        'game_type': 'matching',
        'title': 'Uniendo Términos Matemáticos',
        'instruction': 'Une cada término con su significado correspondiente.',
        'content_json': {
            'pairs': [
                {'left': 'Numerador', 'right': 'Partes que se toman de la unidad'},
                {'left': 'Denominador', 'right': 'Total de partes iguales en que se divide'},
                {'left': 'Fracción propia', 'right': 'El numerador es menor que el denominador'},
            ],
            'explanation': 'Cada elemento de la fracción tiene una función específica en matemáticas.',
        },
        'status': 'PENDING_REVIEW',
        'created_by': 1,
        'created_at': '2026-09-18T13:00:00',
    },
]


