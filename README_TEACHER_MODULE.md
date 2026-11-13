# Módulo del profesor

## Estructura funcional

- Modelo: `models/teacher_model.py`
- Servicios: `services/teacher_service.py`, `services/teacher_assessment_service.py`, `services/teacher_note_service.py`, `services/teacher_reports_service.py`
- Controladores: `controllers/teacher_controller.py`, `controllers/teacher_assessment_controller.py`, `controllers/teacher_notes_controller.py`, `controllers/teacher_reports_controller.py`

## Flujo principal

1. El profesor escribe un tema y selecciona el grado.
2. El sistema genera contenido con IA. 
3. El contenido queda listo para revisarse, editarse y publicarse.
4. El docente puede generar evaluaciones con número de preguntas y nivel de dificultad.
5. El sistema registra notas por estudiante y genera análisis de riesgo.
6. Se exponen reportes resumidos por grado y por estudiante.

## Endpoints

- `POST /teacher/api/generate-topic`
- `POST /teacher/api/generate-preview`
- `POST /teacher/api/assessment/generate`
- `POST /teacher/api/assessment/grade`
- `POST /teacher/api/notes/summary`
- `GET /teacher/api/reports/summary`
- `POST /teacher/api/reports/student-risk`
