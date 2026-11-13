# Módulo del profesor — versión funcional

## Incluye

- Dashboard con métricas clave
- Generación con IA de temas educativos
- CRUD base para temas y contenidos
- Actividades automáticas con respuestas y puntajes
- Evaluaciones generadas por IA
- Registro de notas por actividad, juego y evaluación
- Análisis inteligente por estudiante
- Reportes por grado, estudiante y tema
- Exportación a CSV/Excel-like y PDF textual

## Endpoints activos

- `POST /teacher/api/generate-topic`
- `POST /teacher/api/generate-preview`
- `POST /teacher/api/assessment/generate`
- `POST /teacher/api/assessment/grade`
- `POST /teacher/api/notes/summary`
- `GET /teacher/api/reports/summary`
- `POST /teacher/api/reports/student-risk`
- `POST /teacher/api/reports/export/excel`
- `POST /teacher/api/reports/export/pdf`

## Archivos principales

- `controllers/teacher_controller.py`
- `controllers/teacher_assessment_controller.py`
- `controllers/teacher_notes_controller.py`
- `controllers/teacher_reports_controller.py`
- `controllers/teacher_export_controller.py`
- `services/teacher_service.py`
- `services/teacher_assessment_service.py`
- `services/teacher_note_service.py`
- `services/teacher_reports_service.py`
- `services/teacher_export_service.py`
- `services/teacher_student_intelligence_service.py`

## Nota

Esta implementación deja el módulo conectado y preparado para MySQL o modo mock, sin sustituir la funcionalidad real con datos artificiales como único flujo.
