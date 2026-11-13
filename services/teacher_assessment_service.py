from __future__ import annotations

from typing import Any, Dict, List


def generate_assessment(topic: str, grade: int, question_count: int, difficulty: str) -> Dict[str, Any]:
    title = (topic or '').strip() or 'Tema nuevo'
    grade_value = int(grade) if grade else 5
    count = max(1, int(question_count) if question_count else 3)
    difficulty_name = (difficulty or 'media').lower()

    questions = []
    for idx in range(1, count + 1):
        questions.append({
            'id': idx,
            'question': f'Pregunta {idx}: ¿Cuál es la respuesta correcta sobre {title} para {grade_value}° grado?',
            'options': ['Opción A', 'Opción B', 'Opción C', 'Opción D'],
            'answer': 'Opción A',
            'difficulty': difficulty_name,
            'points': 10,
        })

    return {
        'topic': title,
        'grade': grade_value,
        'difficulty': difficulty_name,
        'question_count': count,
        'questions': questions,
    }


def grade_assessment(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_points = 0
    correct = 0
    for item in submissions or []:
        points = int(item.get('points', 0) or 0)
        total_points += points
        if item.get('correct') is True:
            correct += 1

    score = sum(int(item.get('points', 0) or 0) for item in submissions or [] if item.get('correct') is True)
    percentage = round((score / total_points * 100), 2) if total_points else 0.0

    return {
        'score': score,
        'correct_answers': correct,
        'wrong_answers': len(submissions or []) - correct,
        'percentage': percentage,
        'total_points': total_points,
    }


def generate_formal_15_assessment_questions(topic_title: str, grade: int = 5) -> List[Dict[str, Any]]:
    """
    Genera un banco canónico de exactamente 15 preguntas pedagógicas para la evaluación formal.
    Cada pregunta tiene enunciado, 3 alternativas (A, B, C), respuesta correcta y subtema formativo
    asociado (para retroalimentación diagnóstica de 'Temas a reforzar' cuando el alumno falla).
    """
    title = (topic_title or '').strip() or 'Tema General'
    lower = title.lower()

    if 'fracci' in lower or 'matem' in lower or 'nÃºmero' in lower or 'numero' in lower:
        # Banco de 15 preguntas de Fracciones y Aritmética
        subtopics_map = [
            ("Conceptos de fracciones", "¿Qué representa el numerador en una fracción?", "Las partes que se toman de la unidad", "El total de partes en que se divide el todo", "La suma de los denominadores", "Las partes que se toman de la unidad"),
            ("Conceptos de fracciones", "¿Qué representa el denominador en una fracción?", "El total de partes iguales en que se divide la unidad", "Las partes pintadas de una figura", "Una resta entre números", "El total de partes iguales en que se divide la unidad"),
            ("Tipos de fracciones", "¿Cuál es una característica de una fracción propia?", "El numerador es menor que el denominador (ej. 3/5)", "El numerador es mayor que el denominador", "El numerador y denominador son iguales", "El numerador es menor que el denominador (ej. 3/5)"),
            ("Suma de fracciones", "¿Cuál es el resultado de sumar 3/8 + 2/8?", "5/8", "5/16", "6/8", "5/8"),
            ("Resta de fracciones", "¿Cuál es el resultado de restar 7/10 - 4/10?", "3/10", "3/0", "3/20", "3/10"),
            ("Multiplicación", "¿Cómo se resuelve la multiplicación de fracciones 2/3 x 5/7?", "Multiplicando numeradores entre sí y denominadores entre sí (10/21)", "Multiplicando en cruz", "Sumando los numeradores y restando denominadores", "Multiplicando numeradores entre sí y denominadores entre sí (10/21)"),
            ("Multiplicación", "¿Cuánto es el producto de 4 x 3/5?", "12/5", "12/20", "7/5", "12/5"),
            ("Multiplicación", "Si una botella contiene 3/4 de litro de jugo, ¿cuánto jugo hay en 4 botellas iguales?", "3 litros (12/4)", "7/4 de litro", "3/16 de litro", "3 litros (12/4)"),
            ("División", "¿Cuál es el método para dividir una fracción entre otra como (2/5) ÷ (3/4)?", "Multiplicar la primera fracción por la inversa de la segunda (2/5 x 4/3 = 8/15)", "Dividir numeradores y restar denominadores", "Multiplicar directamente numeradores", "Multiplicar la primera fracción por la inversa de la segunda (2/5 x 4/3 = 8/15)"),
            ("División", "¿Cuál es el resultado de resolver (3/4) ÷ (1/2)?", "6/4 (simplificado a 3/2)", "3/8", "1/2", "6/4 (simplificado a 3/2)"),
            ("División", "Si repartimos 4/5 de un pastel en porciones de 1/10 cada una, ¿cuántas porciones se obtienen?", "8 porciones", "4 porciones", "2 porciones", "8 porciones"),
            ("Simplificación", "¿Cuál es la fracción irreducible al simplificar 12/16 dividiendo entre 4?", "3/4", "6/8", "2/3", "3/4"),
            ("Equivalencia", "¿Cuál de las siguientes fracciones es equivalente a 2/5?", "6/15", "4/15", "2/10", "6/15"),
            ("Comparación", "Entre 5/6 y 2/6, ¿cuál afirmación es correcta?", "5/6 es mayor porque al tener igual denominador, gana el mayor numerador", "2/6 es mayor", "Ambas fracciones tienen el mismo valor", "5/6 es mayor porque al tener igual denominador, gana el mayor numerador"),
            ("Números mixtos", "¿Cómo se expresa la fracción impropia 9/4 como número mixto?", "2 enteros y 1/4", "3 enteros y 1/2", "1 entero y 5/4", "2 enteros y 1/4"),
        ]
    elif 'comput' in lower or 'power' in lower or 'word' in lower or 'capcut' in lower or 'video' in lower:
        # Banco de 15 preguntas de Computación y Tecnología
        subtopics_map = [
            ("Hardware y Periféricos", "¿Qué componente se considera un periférico de entrada?", "El teclado y el mouse", "El monitor", "La impresora", "El teclado y el mouse"),
            ("Software y Sistema Operativo", "¿Qué es el sistema operativo en una computadora?", "El programa principal que gestiona el hardware y las aplicaciones", "Un cable de conexión eléctrica", "Un juego de video", "El programa principal que gestiona el hardware y las aplicaciones"),
            ("Procesador de Textos", "¿Qué herramienta permite cambiar el estilo y color de los títulos?", "Formato de fuente y estilos", "La papelera de reciclaje", "El regulador de volumen", "Formato de fuente y estilos"),
            ("Presentaciones Digitales", "¿Cuál es el objetivo principal de una diapositiva en una presentación?", "Comunicar una idea clave con apoyo visual y poco texto", "Copiar libros enteros en una sola pantalla", "Apagar el proyector", "Comunicar una idea clave con apoyo visual y poco texto"),
            ("Edición de Video", "¿Qué ventaja ofrece el formato vertical 9:16 en videos modernos?", "Es ideal para visualización en teléfonos móviles y formato flyer", "Solo se puede ver en televisores cuadrados", "No permite incluir sonido", "Es ideal para visualización en teléfonos móviles y formato flyer"),
            ("Edición de Video", "¿Qué significa exportar un proyecto multimedia terminado?", "Convertirlo a un formato reproducible final como MP4", "Borrar todas las fotos del disco", "Imprimirlo en hojas", "Convertirlo a un formato reproducible final como MP4"),
            ("Imágenes Digitales", "¿Qué característica distingue a los archivos gráficos PNG?", "Soportan fondo transparente para superponer elementos", "Tienen música de fondo obligatoria", "No se pueden abrir en computadoras", "Soportan fondo transparente para superponer elementos"),
            ("Almacenamiento en La Nube", "¿Qué ventaja tiene guardar archivos en La Nube?", "Acceder a ellos desde cualquier dispositivo conectado a Internet", "Ocupan espacio en la memoria física del monitor", "Solo funcionan cuando está lloviendo", "Acceder a ellos desde cualquier dispositivo conectado a Internet"),
            ("Seguridad Digital", "¿Cuál es una práctica segura para proteger tus cuentas?", "Crear contraseñas seguras y no compartirlas", "Escribir la clave en el escritorio público", "Usar siempre 123456 en todas partes", "Crear contraseñas seguras y no compartirlas"),
            ("Organización de Archivos", "¿Para qué se crean carpetas y subcarpetas en el explorador?", "Para clasificar y encontrar los trabajos de forma ordenada", "Para llenar la memoria de la máquina", "Para cambiar el idioma del teclado", "Para clasificar y encontrar los trabajos de forma ordenada"),
            ("Internet y Búsquedas", "¿Qué se debe verificar al buscar información en la web para una tarea?", "Que la fuente sea confiable, educativa o institucional", "Que tenga muchos anuncios comerciales", "Copiar lo primero que aparezca sin leer", "Que la fuente sea confiable, educativa o institucional"),
            ("Atajos de Teclado", "¿Cuál es el atajo universal para guardar un archivo en aplicaciones?", "Control + G (o Ctrl + S)", "Control + Alt + Supr", "Barra espaciadora", "Control + G (o Ctrl + S)"),
            ("Herramientas Colaborativas", "¿Qué permite hacer un documento compartido en línea?", "Trabajar en equipo al mismo tiempo desde distintas computadoras", "Bloquear la pantalla de los demás", "Apagar los equipos de los compañeros", "Trabajar en equipo al mismo tiempo desde distintas computadoras"),
            ("Código QR", "¿Qué función cumple un código QR en una ficha informativa?", "Enlazar de forma rápida a un video, sitio o documento en línea", "Reemplazar la pantalla del celular", "Borrar el historial de navegación", "Enlazar de forma rápida a un video, sitio o documento en línea"),
            ("Uso Responsable de Tecnología", "¿Cuál es una norma de convivencia digital adecuada en el aula?", "Respetar a los compañeros y cuidar los equipos de cómputo", "Descargar juegos sin permiso del docente", "Desconectar los cables del laboratorio", "Respetar a los compañeros y cuidar los equipos de cómputo"),
        ]
    else:
        # Banco general de 15 preguntas
        categories = ["Conceptos fundamentales", "Comprensión del proceso", "Aplicación práctica", "Análisis de casos", "Resolución de problemas"]
        subtopics_map = []
        for i in range(1, 16):
            cat = categories[(i - 1) % len(categories)]
            subtopics_map.append((
                cat,
                f"Pregunta {i} sobre {title}: ¿Cuál de las siguientes afirmaciones describe adecuadamente este concepto?",
                f"La afirmación correcta que define los principios clave de {title}",
                f"Una descripción incompleta que no corresponde a {title}",
                f"Una opción incorrecta o ajena a los objetivos de {title}",
                f"La afirmación correcta que define los principios clave de {title}",
            ))

    questions = []
    for idx, (subtopic, q_text, opt_a, opt_b, opt_c, ans) in enumerate(subtopics_map[:15], 1):
        questions.append({
            'id': idx,
            'question': q_text,
            'option_a': opt_a,
            'option_b': opt_b,
            'option_c': opt_c,
            'options': [opt_a, opt_b, opt_c],
            'answer': ans,
            'subtopic': subtopic,
            'approved': True,
            'score': 2,
        })

    return questions

