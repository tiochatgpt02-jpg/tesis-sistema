# Revisión de la arquitectura actual

Actualizado el 16 de noviembre de 2026. Este resumen sustituye un documento heredado que no debe utilizarse como evidencia de la publicación actual. Sus rutas locales y conclusiones no verificadas se retiraron de la documentación pública.

## Estructura observada

La aplicación es un monolito modular Flask con Blueprints. controllers contiene rutas y autorización, services reúne reglas y persistencia, views contiene plantillas Jinja y static/js controla la interacción. PostgreSQL remoto conserva usuarios, materiales, intentos, resultados, calendario e historial.

La generación usa Groq; NVIDIA es una alternativa configurable. No se requiere Ollama local para el despliegue. El docente revisa y publica contenido; las respuestas del alumno se califican con datos guardados y preguntas congeladas.

## Módulos para ubicar código

| Función | Ubicación |
| --- | --- |
| Juegos desde PPT | services/material_extractor_service.py y ai_game_generator_service.py |
| Formularios de juego | static/js/teacher_game_editor.js |
| Evaluaciones | controllers/student_assessment_controller.py y services/learning_attempt_service.py |
| Libreta | services/bimester_grade_service.py y grading_policy_service.py |
| Calendario y cierre | academic_calendar_service.py y academic_closure_service.py |
| Historial literal | services/literal_history_service.py |
| Variables ML | ml/pipeline/feature_builder.py |
| Selección y evaluación ML | ml/pipeline/trainer.py |
| Inferencia | ml/pipeline/predictor.py y services/ml/prediction_service.py |

## Límites y decisiones

El despliegue utiliza Render Free y Neon. La suspensión y el despertar del plan gratuito limitan su disponibilidad. Los archivos pequeños también se conservan en PostgreSQL; un aumento sostenido de usuarios y archivos requeriría revisar almacenamiento y capacidad.

La base de código conserva controladores y un archivo de persistencia grandes. La mejora recomendada es separarlos por dominio con contratos y pruebas, manteniendo el monolito mientras el tamaño del piloto no justifique más complejidad operativa.

El modelo de referencia se entrenó con un solo curso público de UCI. Selección interna y prueba final están separadas. No acredita precisión institucional. El historial AD/A/B/C del colegio permanece separado y no se convierte a notas numéricas.

Las comprobaciones locales registraron 222 pruebas aprobadas y tres integraciones omitidas por defecto; se ejecutó además una integración PostgreSQL aislada. Estos resultados verifican casos concretos, no cobertura completa del producto ni un piloto humano.

El [expediente TOGAF 9.2](arquitectura-togaf-9-2.md) contiene actores, procesos, dominios, brechas, decisiones y gobierno adaptados. La aceptación institucional, el material oficial por grado y la validación temporal con datos posteriores siguen pendientes de evidencia externa.
