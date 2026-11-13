# Auditoría Profunda de Arquitectura Actual del Sistema IA Educativo

**Fecha de Auditoría:** 19 de Septiembre de 2026  
**Objetivo:** Documento técnico base y radiografía integral del estado del código fuente del proyecto Sistema IA para la toma de decisiones arquitectónicas en futuras fases de desarrollo.  
**Restricción Cumplida:** Auditoría de solo lectura. No se aplicaron modificaciones, refactorizaciones ni alteraciones al código fuente ni a las bases de datos.

---

## 1. Resumen Ejecutivo

El **Sistema IA Educativo** es una plataforma web monolítica orientada a instituciones de educación básica regular (primaria) para la enseñanza y seguimiento en el área de Computación y áreas afines. La solución combina tres componentes tecnológicos principales:
1. **Un núcleo web interactivo** desarrollado en **Python (Flask 3.1.3)** estructurado bajo un patrón en capas (Controllers, Services, Views/Templates Jinja2, Static JS/CSS).
2. **Un subsistema de Machine Learning clásico (scikit-learn 1.9.1)** con un clasificador supervisado **Random Forest** para la detección temprana y explicable del riesgo de reprobación académica del estudiante (sensibilidad del 90.48% y ROC-AUC de 0.9605 sobre dataset benchmark UCI con paridad estricta hacia datos institucionales).
3. **Un subsistema de Inteligencia Artificial Generativa** integrado con **Ollama (`llama3`)** y opcionalmente **OpenAI (GPT-3.5-Turbo)** para la generación curricular de planes de estudio, lecturas formativas basadas estrictamente en texto docente, retos lúdicos multinivel y evaluaciones estructuradas.

### Principales Fortalezas Encontradas
- **Cobertura de Pruebas Automatizadas Rigurosa:** Cuenta con 81 pruebas unitarias y de integración (`pytest 9.1.1`) que verifican el 100% de los flujos críticos (ML, evaluaciones, juegos, materiales, aprobación docente y motor adaptativo).
- **Protección Antifuga Temporal (Anti-Leakage) en ML:** Separación estricta de variables con fecha de corte (`cutoff_date`), anonimización de identificadores personales en la matriz de features y congelamiento de esquema canónico de 18 variables en `features.json`.
- **Modo Demostración Offline Robusto:** Capacidad de operar fluidamente sin conectividad a MySQL o a servicios de IA remotos mediante un almacén de datos mock en memoria y bancos de contenido de contingencia.
- **Aprendizaje Adaptativo Unificado (GOAL 6):** Orquestación exitosa que vincula Calificaciones + Evaluaciones + Juegos Lúdicos + Predicción ML en un diagnóstico objetivo y plan de 3 pasos (Lectura $\to$ Juego $\to$ Evaluación).

### Principales Deudas Técnicas y Riesgos
- **Seguridad y Autenticación:** Verificación de contraseñas en texto plano (`password == user.get('password_hash')`) sin funciones hash criptográficas (bcrypt/Argon2). Bloque de código inalcanzable (dead code) en la verificación de dos factores de `auth_controller.py`.
- **Monolito en Capa de Datos (`db_service.py`):** Un único archivo de más de 2,010 líneas y 83 funciones que gestiona todas las entidades del dominio con sintaxis SQL específica de MySQL (`%s`, `AUTO_INCREMENT`), lo que dificulta una migración directa a PostgreSQL.
- **Inconsistencias en Esquema DDL (`sql/schema.sql`):** La tabla `alerts` es consultada en el código pero no está declarada en el script SQL de creación. Existen 7 tablas huérfanas en el DDL que nunca son consumidas por la aplicación (`teacher_topics`, `teacher_activities`, `teacher_games`, `teacher_evaluaciones`, `grades`, `student_results`, `teacher_recommendations`).
- **Monolitos Frontend en JavaScript:** `teacher.js` (126 KB) y `student.js` (107 KB) concentran toda la interacción de interfaz, temporizadores, parseo de DOM y llamadas AJAX en archivos únicos sin modularización ES6.
- **Modelos de Dominio Huérfanos (`models/`):** Las clases en `models/` (`User`, `Topic`, `Teacher`) no son importadas ni utilizadas en ningún punto de la plataforma; el sistema opera exclusivamente mediante diccionarios dinámicos (`dict`).

---

## 2. Árbol del Proyecto y Organización de Carpetas

```text
c:\Users\familia\Downloads\sistema IA\sistema IA/
├── app.py                         # Punto de entrada de la aplicación Flask y configuración de Blueprints
├── config.py                      # Clase de configuración centralizada y lectura de variables de entorno (.env)
├── .env                           # Variables de entorno locales activas (credenciales, host, puertos)
├── .env.example                   # Plantilla de configuración documentada para despliegues externos
├── requirements.txt               # Declaración de dependencias Python principales
├── verify_system.py               # Script de auditoría integral del sistema (BD, ML, Pipeline, Rutas)
├── iniciar_sistema.bat            # Script de conveniencia para lanzamiento en entorno Windows
├── pytest.ini                     # Configuración base para el ejecutor de pruebas pytest
│
├── controllers/                   # Capa de Controladores (Flask Blueprints)
│   ├── auth_controller.py         # Autenticación, inicio de sesión, sesiones y redirección por rol
│   ├── teacher_controller.py      # Panel docente, gestión de alumnos, temas, presentaciones y mensajería
│   ├── teacher_assessment_controller.py # Flujo de aprobación docente de evaluaciones IA (GENERATED -> PUBLISHED)
│   ├── teacher_notes_controller.py# Cuaderno de notas y reportes consolidados por estudiante
│   ├── teacher_reports_controller.py # Análisis predictivo de riesgo, generación y descarga de reportes
│   ├── teacher_export_controller.py # Endpoints de exportación a formatos Excel (.xlsx) y PDF
│   ├── student_controller.py      # Portal del estudiante, progreso, materiales, exámenes, juegos y ML
│   └── ai_controller.py           # Endpoints públicos/docentes de generación lúdica y consulta Ollama
│
├── services/                      # Capa de Lógica de Negocio y Servicios del Dominio
│   ├── db_service.py              # Acceso a base de datos (MySQL) con fallback a modo demostración
│   ├── mock_data.py               # Almacén de datos simulados en memoria para ejecución offline
│   ├── ai_service.py              # Integración con Ollama (local) y OpenAI, generación de packs y prompts
│   ├── ml_service.py              # Fachada de integración de predicción y métricas para vistas Flask
│   ├── adaptive_recommendations_service.py # Unificación adaptativa (Notas + Evaluaciones + Juegos + ML)
│   ├── reinforcement_games_service.py      # Lógica de los 3 juegos lúdicos y recomendación por debilidad
│   ├── student_learning_service.py# Construcción de lecciones, evaluación y progreso formativo del alumno
│   ├── teacher_service.py         # Resumen del dashboard docente y generación de bancos de preguntas
│   ├── teacher_assessment_service.py # Generación y calificación de evaluaciones docentes de 15 preguntas
│   ├── teacher_reports_service.py # Cálculo de promedios, escalas vigesimales y niveles de logro
│   ├── teacher_export_service.py  # Construcción de libros Excel (.xlsx) y documentos imprimibles
│   ├── teacher_student_intelligence_service.py # Análisis de fortalezas y riesgos del alumno
│   ├── teacher_note_service.py    # Consolidación del libro de notas del profesor
│   ├── grade_service.py           # Conversiones matemáticas de escalas (0-100% a 0-20 vigesimal)
│   ├── email_service.py           # Notificaciones simuladas/reales por correo y SMS (Twilio)
│   ├── two_step_service.py        # Generador y validador de códigos de verificación temporal
│   └── ml/                        # Subcapa de servicios de inferencia ML
│       ├── __init__.py
│       ├── feature_service.py     # Extracción y aislamiento de características del estudiante
│       ├── model_registry.py      # Carga, selección de fuente (benchmark/institucional) y caché de modelos
│       └── prediction_service.py  # Orquestador de inferencia y motor de explicabilidad pedagógica
│
├── ml/                            # Subsistema Central de Machine Learning (Offline & Pipeline)
│   ├── run_pipeline.py            # Comando único de orquestación del pipeline (entrenamiento y validación)
│   ├── datasets/                  # Datasets de entrenamiento (benchmark UCI y plantilla institucional)
│   │   ├── student-mat.csv        # Dataset benchmark internacional preprocesado
│   │   └── student_notes_example.csv # Plantilla de datos históricos de calificaciones
│   ├── models/                    # Artefactos serializados y metadatos del modelo
│   │   ├── metadata.json          # Metadatos del modelo activo en producción
│   │   ├── student_risk_pipeline.joblib # Pipeline serializado completo
│   │   ├── benchmark/             # Artefactos del modelo entrenado sobre benchmark UCI
│   │   │   ├── model.joblib       # Clasificador Random Forest serializado
│   │   │   ├── features.json      # Esquema canónico congelado de 18 variables
│   │   │   ├── metadata.json      # Métricas de validación (Recall: 90.48%, AUC: 0.9605)
│   │   │   ├── training_results.json # Registro de experimentos y comparación de modelos
│   │   │   └── validation_metadata.json # Configuración de partición temporal
│   │   └── institutional/         # Espacio reservado para datos de la propia escuela (sin entrenar)
│   │       └── metadata.json      # Estado: not_trained con advertencia metodológica
│   └── pipeline/                  # Componentes modulares del pipeline ML
│       ├── __init__.py
│       ├── data_loader.py         # Carga y validación rigurosa de matrices CSV y tipos de datos
│       ├── preprocessing.py       # Pipelines de imputación y escalamiento (StandardScaler)
│       ├── feature_builder.py     # Construcción canónica de features con corte temporal anti-fuga
│       ├── trainer.py             # Entrenamiento supervisado, partición cronológica y ajuste de hiperparámetros
│       ├── evaluator.py           # Cálculo de métricas estándar (Recall, Precision, F1, ROC-AUC)
│       └── predictor.py           # Inferencia explicable y mapeo a factores pedagógicos comprensibles
│
├── models/                        # Entidades POPO (Plain Old Python Objects) - Actualmente Huérfanas
│   ├── user_model.py              # Clase User (no importada en controladores)
│   ├── topic_model.py             # Clase Topic (no importada en controladores)
│   └── teacher_model.py           # Clase Teacher (no importada en controladores)
│
├── sql/                           # Definición de Esquema de Base de Datos y Scripts SQL
│   ├── schema.sql                 # DDL principal de tablas para MySQL
│   ├── migrate.sql                # Script auxiliar de migración manual
│   ├── fix_public_private.sql     # Script de ajuste de visibilidad de temas
│   └── migrations/                # Carpeta de migraciones secuenciales
│       └── 001_create_academic_outcomes.sql # Creación de tabla de resultados académicos
│
├── views/                         # Plantillas Jinja2 (HTML)
│   ├── login.html                 # Pantalla de autenticación de usuarios
│   ├── two_step.html              # Pantalla de verificación de doble factor
│   ├── teacher_dashboard.html     # Dashboard integral docente (SPA con pestañas dinámicas)
│   ├── student_dashboard.html     # Dashboard integral del estudiante (SPA con pestañas dinámicas)
│   ├── ml_status.html             # Pantalla de transparencia técnica del estado del modelo ML
│   ├── student_juegos.html        # Vista interactiva de juegos generados por IA
│   ├── teacher_reports.html       # Vista de reportes de rendimiento y calificaciones
│   ├── teacher_students.html      # (Legacy) Vista aislada de alumnos
│   ├── teacher_topics.html        # (Legacy) Vista aislada de temas
│   ├── student_topics.html        # (Legacy) Redirecciona al dashboard de estudiante
│   ├── student_progress.html      # (Legacy) Redirecciona al dashboard de estudiante
│   └── dashboard.html             # (Legacy) Redirecciona según el rol autenticado
│
├── static/                        # Recursos Estáticos del Navegador
│   ├── css/                       # Hojas de estilo personalizadas
│   │   ├── styles.css             # Estilos generales del sistema y vista docente
│   │   ├── student.css            # Estilos específicos del aula virtual del estudiante
│   │   └── teacher_reports.css    # Estilos del módulo de analíticas y reportes
│   ├── js/                        # Lógica del Frontend (Vanilla JavaScript)
│   │   ├── teacher.js             # Monolito JS docente (126 KB): interacción, modales, AJAX
│   │   ├── student.js             # Monolito JS alumno (107 KB): juegos, exámenes, progreso, adaptativo
│   │   └── teacher_reports.js     # Gráficos e interactividad de reportes analíticos
│   ├── img/                       # Ilustraciones SVG y recursos visuales educativos
│   └── uploads/                   # Directorio de subida de presentaciones (.pptx) y tareas
│
├── tests/                         # Suite de Pruebas Automatizadas (81 Tests)
│   ├── test_ml_pipeline.py        # Validación del pipeline ML, data loader y prevención de fugas
│   ├── test_ml_refactor.py        # Pruebas de paridad, normalización vigesimal y reproducibilidad
│   ├── test_student_risk_prediction.py # Predicción para estudiantes y control de acceso
│   ├── test_adaptive_recommendations.py # Motor de recomendaciones unificadas (4 pilares)
│   ├── test_assessment_approval_workflow.py # Estados de aprobación docente de exámenes IA
│   ├── test_fifteen_questions_assessment.py # Examen formal único de 15 preguntas
│   ├── test_reinforcement_games.py# Catálogo y lógica de los 3 juegos lúdicos interactivos
│   ├── test_teacher_student_materials.py # Publicación de material docente y práctica con IA
│   ├── test_teacher_assessment_and_notes.py # Calificación de evaluaciones y cuaderno de notas
│   ├── test_teacher_export_and_student_analysis.py # Exportación a Excel/PDF y análisis formativo
│   ├── test_teacher_module.py     # Generación de temas y banco de preguntas
│   ├── test_teacher_reports.py    # Reportes consolidados y predicciones docentes
│   └── test_db_service.py         # Verificación de integridad de esquema y aislamiento
│
├── scripts/                       # Scripts de Utilidad y Mantenimiento
│   ├── setup_db.py                # Inicializador de base de datos MySQL local
│   ├── test_db.py                 # Comprobador rápido de conexión a MySQL
│   ├── test_preview.py            # Prueba de previsualización de contenidos
│   ├── test_preview_noauth.py     # Prueba de acceso no autenticado
│   └── verify_topics_flow.py      # Verificación del ciclo de vida de temas
│
└── legacy/                        # Archivos Históricos Desacoplados (No activos en producción)
    ├── README_LEGACY.md           # Explicación de componentes archivados
    ├── teacher_module_service.py  # Versión anterior de funciones docentes
    ├── mi-app_vite_starter/       # Esqueleto inicial React Vite no conectado a Flask
    └── sistema_ia_v1_nested/      # Copia redundante y obsoleta del proyecto inicial
```

---

## 3. Arquitectura Backend

El backend está construido con **Python 3.12** utilizando el microframework **Flask 3.1.3**. La aplicación adopta un patrón en capas desacoplado mediante **Flask Blueprints**.

### Flujo Canónico de una Petición HTTP

```text
       Navegador Web (Cliente)
                  │
                  ▼ [Petición HTTP / JSON]
         ┌──────────────────┐
         │      app.py      │  (Configuración, sesión cookie, filtros Jinja2)
         └────────┬─────────┘
                  │ Enrutamiento por prefijo de Blueprint
                  ▼
         ┌──────────────────┐
         │ Capa Controllers │  (ej: student_controller.py, teacher_controller.py)
         │ - Validación rol │
         │ - Parseo entrada │
         └────────┬─────────┘
                  │ Invocación directa de funciones
                  ▼
         ┌──────────────────┐
         │  Capa Services   │  (ej: adaptive_recommendations_service.py, ai_service.py)
         │ - Reglas negocio │
         │ - Orquestación   │
         └────┬────────┬────┘
              │        │
     ┌────────┴┐      ┌┴────────────────┐
     ▼         ▼      ▼                 ▼
┌─────────┐ ┌────┐ ┌─────┐ ┌─────────────────────────┐
│db_servic│ │Olla│ │OpenA│ │services/ml/ (ML Service) │
│e (MySQL)│ │ma  │ │I    │ │  -> Random Forest Model │
└─────────┘ └────┘ └─────┘ └─────────────────────────┘
              │        │
              └────────┼────────────────┐
                       ▼                ▼
         ┌──────────────────┐  ┌──────────────────┐
         │  Respuesta JSON  │  │  Render Template │
         │  (API REST)      │  │  (Jinja2 HTML)   │
         └────────┬─────────┘  └────────┬─────────┘
                  │                     │
                  └──────────┬──────────┘
                             ▼
                  Navegador Web (Cliente)
```

### Punto de Entrada y Módulos Registrados en `app.py`

| Archivo | Responsabilidad Arquitectónica |
|---|---|
| [`app.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/app.py) | Inicializa la instancia `Flask(__name__, template_folder='views', static_folder='static')`, asigna `secret_key`, registra el filtro Jinja2 `plain_summary`, registra los 8 Blueprints, expone la ruta `/health` y arranca el servidor WSGI de desarrollo (`debug=True`). |
| [`config.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/config.py) | Centraliza la configuración mediante la clase `Config`. Lee variables de entorno mediante `python-dotenv` para credenciales MySQL, claves de OpenAI, endpoints de Ollama (`http://127.0.0.1:11434`), modelo local (`llama3`), credenciales Twilio y bandera de fallback `USE_MOCK_DATA`. |
| `controllers/auth_controller.py` | Prefijo `/`. Controla inicio y cierre de sesión, verificación de credenciales y redirección por rol. |
| `controllers/teacher_controller.py` | Prefijo `/teacher`. Controlador principal docente para la gestión académica, estudiantes, temas y presentaciones. |
| `controllers/teacher_assessment_controller.py` | Prefijo `/teacher`. Ciclo de vida y aprobación pedagógica de evaluaciones IA (`GENERATED` $\to$ `PENDING_REVIEW` $\to$ `APPROVED` $\to$ `PUBLISHED`). |
| `controllers/teacher_notes_controller.py` | Prefijo `/teacher`. Gestión de notas y resúmenes de calificaciones por alumno. |
| `controllers/teacher_reports_controller.py` | Prefijo `/teacher`. Generación de reportes analíticos, estimaciones de riesgo y descargas. |
| `controllers/teacher_export_controller.py` | Prefijo `/teacher`. Exportación formal de actas de notas a formato Excel (.xlsx) y PDF. |
| `controllers/student_controller.py` | Prefijo `/student`. Portal completo del estudiante: lecciones, materiales, práctica con IA, examen de 15 preguntas, juegos interactivos y recomendaciones adaptativas. |
| `controllers/ai_controller.py` | Prefijo `/ai`. Endpoints para generación de juegos de 3 niveles con Ollama y estado de la IA. |

---

## 4. Análisis Detallado de Controladores (Controllers)

A continuación se auditan los 8 controladores del sistema, detallando sus rutas, métodos HTTP, servicios invocados, entradas y salidas.

### 4.1. `auth_controller.py`
- **Responsabilidad:** Autenticación de usuarios, manejo de sesiones Flask y redirección según rol (`teacher` o `student`).
- **Dependencias:** `services.db_service`, `services.mock_data`, `services.email_service`, `services.two_step_service`, `config.Config`.

| Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|
| `/` | `GET` | `index` | Ninguno | Redirección 302 a `/login` |
| `/login` | `GET` | `login` | Ninguno | Renderiza `views/login.html` |
| `/login` | `POST` | `login` | `username`, `password` (Form) | Si es válido: crea sesión de Flask y redirige a `/teacher` o `/student`. Si falla: renderiza `login.html` con mensaje de error. *(Nota: Contiene código 2FA inalcanzable)* |
| `/two-step` | `GET`, `POST` | `two_step` | `code` (Form) | Valida código temporal. Redirige según rol o renderiza `views/two_step.html` |
| `/dashboard` | `GET` | `dashboard` | Cookie de sesión | Redirección 302 según `session['user_role']` a `/teacher` o `/student` |
| `/logout` | `GET` | `logout` | Ninguno | `session.clear()`, redirección 302 a `/login` |

---

### 4.2. `teacher_controller.py`
- **Responsabilidad:** Administración de estudiantes, asignación curricular de temas, subida de presentaciones, bandeja de mensajes y revisión de tareas.
- **Dependencias:** `services.db_service`, `services.ai_service`, `services.ml_service`, `services.teacher_service`, `services.teacher_reports_service`.

| Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|
| `/teacher/` | `GET` | `teacher_home` | Sesión activa (`role=teacher`) | Renderiza `views/teacher_dashboard.html` con estudiantes, temas y métricas |
| `/teacher/students` | `GET` | `manage_students` | Sesión activa | Renderiza `views/teacher_students.html` |
| `/teacher/topics` | `GET` | `teacher_topics` | Sesión activa | Renderiza `views/teacher_topics.html` |
| `/teacher/reports` | `GET` | `teacher_reports` | Sesión activa | Renderiza `views/teacher_reports.html` con promedios y distribución |
| `/teacher/ml-status` | `GET` | `teacher_ml_status` | Sesión activa | Renderiza `views/ml_status.html` con estado de Random Forest y benchmark UCI |
| `/teacher/api/generate-topic` | `POST` | `api_generate_topic` | `title`, `grade` (JSON) | Genera planificación curricular con OpenAI/Local y retorna JSON `{success, topic_id}` |
| `/teacher/api/generate-preview` | `POST` | `api_generate_preview` | `title`, `grade` (JSON) | Previsualización de planificación sin guardar en BD `{success, preview}` |
| `/teacher/api/predict-student` | `POST` | `api_predict_student` | `features` o `student_id` (JSON) | Inferencia de riesgo académico y factores pedagógicos `{success, risk_level, probability, factors}` |
| `/teacher/api/students/<id>/risk` | `GET` | `api_student_risk` | `student_id` en URL | Predicción de riesgo del estudiante especificado `{success, risk_data}` |
| `/teacher/api/students` | `POST` | `api_create_student` | `first_name`, `last_name`, `grade`, `observations` | Inserta estudiante en BD y retorna JSON `{success, student_id}` |
| `/teacher/api/students/<id>` | `DELETE` | `api_delete_student` | `student_id` en URL | Elimina registro del estudiante `{success, message}` |
| `/teacher/api/students/<id>/observations` | `PUT` | `api_update_student_observations` | `observations` (JSON) | Actualiza observaciones formativas `{success}` |
| `/teacher/api/messages/<id>` | `GET` | `api_get_student_messages` | `student_id` en URL | Lista de mensajes intercambiados con el alumno `{success, messages}` |
| `/teacher/api/messages/<id>` | `DELETE` | `api_delete_message` | `message_id` en URL | Elimina mensaje `{success}` |
| `/teacher/api/submissions` | `GET` | `api_get_submissions` | Query params (`topic_id`) | Lista de tareas y archivos entregados por estudiantes `{success, submissions}` |
| `/teacher/api/submissions/<id>/review` | `PUT` | `api_review_submission` | `grade`, `feedback` (JSON) | Califica entrega del alumno `{success, message}` |
| `/teacher/api/topic/<id>/materials` | `GET`, `POST` | `api_topic_materials` | `topic_id`, `title`, `content` | Consulta o crea material educativo de texto `{success, material_id}` |
| `/teacher/api/materials/<id>` | `DELETE` | `api_delete_material` | `material_id` en URL | Elimina material educativo `{success}` |
| `/teacher/api/materials/<id>/generate-activities` | `POST` | `api_generate_material_activities` | `material_id` en URL | IA genera preguntas basadas estrictamente en el texto del docente |
| `/teacher/api/topic/<id>/learning-items` | `GET`, `POST` | `api_topic_learning_items` | `topic_id` | Consulta o añade actividades/juegos al tema `{success, items}` |
| `/teacher/api/topic/<id>/auto-content` | `POST` | `api_generate_topic_content` | `topic_id` | Genera y guarda automáticamente pack de actividades del tema |
| `/teacher/api/upload-presentation` | `POST` | `api_upload_presentation` | `file` (.pptx), `topic_id` (Form) | Guarda presentación en `/static/uploads/` y registra en BD `{success}` |
| `/teacher/api/presentations/<id>` | `GET` | `api_topic_presentations` | `topic_id` en URL | Lista presentaciones adjuntas al tema `{presentations, success}` |
| `/teacher/api/delete-presentation/<id>` | `DELETE` | `api_delete_presentation` | `presentation_id` en URL | Elimina presentación de BD y disco `{success}` |
| `/teacher/api/learning-items/<type>/<id>` | `DELETE` | `api_delete_learning_item` | `item_type`, `item_id` | Elimina actividad o juego del tema `{success}` |
| `/teacher/api/topic/<id>` | `PUT`, `DELETE` | `api_topic_manage` | `topic_id`, datos a actualizar | Modifica título/estado o elimina tema curricular `{success}` |
| `/teacher/api/send-message` | `POST` | `api_send_message` | `student_id`, `message` (JSON) | Registra mensaje hacia el alumno `{success, message_id}` |
| `/teacher/api/read-messages` | `GET` | `api_get_read_messages` | Sesión activa | Lista mensajes leídos por el docente `{success, messages}` |
| `/teacher/api/alerts` | `GET` | `api_get_alerts` | Sesión activa | Alertas de rendimiento y notificaciones `{success, alerts}` |
| `/teacher/api/alerts/<id>/read` | `PUT` | `api_mark_alert_read` | `alert_id` en URL | Marca alerta como leída `{success}` |

---

### 4.3. `teacher_assessment_controller.py`
- **Responsabilidad:** Implementación del flujo de aprobación y validación docente de preguntas de evaluación (GOAL 3).
- **Dependencias:** `services.db_service`, `services.ai_service`, `services.teacher_assessment_service`.

| Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|
| `/teacher/api/assessment/generate` | `POST` | `api_generate_assessment` | `topic`, `grade` (JSON) | Genera evaluación inicial sin publicar `{success, assessment}` |
| `/teacher/api/assessment/grade` | `POST` | `api_grade_assessment` | `answers`, `correct_answers` | Calificación rápida `{score, percentage}` |
| `/teacher/api/assessments/generate` | `POST` | `api_generate_ai_assessment` | `topic_id`, `title` (JSON) | IA crea examen en estado `PENDING_REVIEW` con preguntas no aprobadas |
| `/teacher/api/assessments` | `GET` | `api_list_assessments` | Query params (`topic_id`) | Lista evaluaciones filtradas con conteo de preguntas y estado |
| `/teacher/api/assessments/<id>` | `GET` | `api_get_assessment` | `assessment_id` en URL | Detalle del examen y todas sus preguntas (aprobadas y no aprobadas) |
| `/teacher/api/assessments/<aid>/questions/<qid>` | `PUT` | `api_update_assessment_question` | `question`, `options`, `answer` | Permite al docente editar enunciado, distractores y respuesta correcta |
| `/teacher/api/assessments/<aid>/questions/<qid>` | `DELETE` | `api_delete_assessment_question` | IDs en URL | Elimina pregunta inadecuada `{success}` |
| `/teacher/api/assessments/<aid>/questions` | `POST` | `api_add_assessment_question` | `question`, `options`, `answer` | Docente añade manualmente una pregunta a la evaluación |
| `/teacher/api/assessments/<aid>/questions/<qid>/approve` | `POST` | `api_approve_single_question` | IDs en URL | Cambia estado de la pregunta a `approved=True` |
| `/teacher/api/assessments/<id>/approve` | `POST` | `api_approve_assessment` | `assessment_id` en URL | Aprueba el examen global (`APPROVED`) si tiene preguntas validadas |
| `/teacher/api/assessments/<id>/publish` | `POST` | `api_publish_assessment` | `assessment_id` en URL | Pasa el examen a `PUBLISHED`. Solo ahora es visible para los alumnos |

---

### 4.4. `teacher_reports_controller.py`, `teacher_notes_controller.py`, `teacher_export_controller.py`
- **Responsabilidad:** Módulo de analíticas, libro de calificaciones, promedios y exportaciones a Excel/PDF.
- **Dependencias:** `services.db_service`, `services.teacher_reports_service`, `services.teacher_export_service`, `services.teacher_note_service`.

| Archivo | Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|---|
| `reports` | `/teacher/api/reports/summary` | `GET` | `api_reports_summary` | Query param `grade` | Consolidado analítico `{kpis, gradebook, distribution}` |
| `reports` | `/teacher/api/reports/gradebook` | `GET` | `api_reports_gradebook` | Query param `grade` | Cuaderno de notas por estudiante `{students, topics}` |
| `reports` | `/teacher/api/reports/export.xlsx` | `GET` | `api_export_excel_file` | Query param `grade` | Archivo binario Excel descargable (`.xlsx`) |
| `reports` | `/teacher/api/reports/student-risk` | `POST` | `api_student_risk` | `student_id`, `grade` | Análisis de fortalezas, debilidades y nivel de riesgo |
| `notes` | `/teacher/api/notes/summary` | `POST` | `api_notes_summary` | `grade` (JSON) | Resumen del consolidado de notas por grado |
| `export` | `/teacher/api/reports/export/excel` | `POST` | `api_export_excel` | `report_data` (JSON) | Genera reporte Excel estructurado |
| `export` | `/teacher/api/reports/export/pdf` | `POST` | `api_export_pdf` | `report_data` (JSON) | Genera documento imprimible / PDF |

---

### 4.5. `student_controller.py`
- **Responsabilidad:** Portal integral del estudiante: consulta de clases, materiales formativos, práctica basada en lecturas, examen único de 15 preguntas, juegos interactivos de reforzamiento, predicción de riesgo y recomendaciones adaptativas.
- **Dependencias:** `services.db_service`, `services.student_learning_service`, `services.reinforcement_games_service`, `services.adaptive_recommendations_service`.

| Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|
| `/student/` | `GET` | `student_home` | Sesión activa (`role=student`) | Renderiza `views/student_dashboard.html` con temas, progreso, riesgo ML y plan adaptativo |
| `/student/api/topics/<id>/lesson` | `GET` | `api_topic_lesson` | `topic_id` en URL | Contenido pedagógico del tema y actividades formativas `{success, lesson}` |
| `/student/api/topics/<id>/materials` | `GET` | `api_topic_materials` | `topic_id` en URL | Recursos educativos asociados al tema |
| `/student/api/topics/<id>/learning-items` | `GET` | `api_student_learning_items` | `topic_id` en URL | Juegos y ejercicios generados disponibles |
| `/student/api/materials` | `GET` | `api_all_student_materials` | Sesión activa | Lista de todos los materiales educativos asignados `{materials, total}` |
| `/student/api/materials/<id>` | `GET` | `api_get_single_material` | `material_id` en URL | Contenido completo de lectura preparado por el profesor `{success, material}` |
| `/student/api/materials/<id>/practice` | `GET` | `api_get_material_practice` | `material_id` en URL | Preguntas generadas por IA basadas estrictamente en el texto del material |
| `/student/api/materials/<id>/practice` | `POST` | `api_submit_material_practice` | `answers` (JSON) | Califica respuestas de lectura, guarda en BD y actualiza estado a Leído |
| `/student/api/materials/<id>/reviewed` | `POST` | `api_mark_material_reviewed` | `material_id` en URL | Marca lectura como completada en `material_reviews` |
| `/student/api/topics/<id>/activity` | `POST` | `api_submit_activity` | `activity_id`, `answer` (JSON) | Califica actividad y registra nota en `student_notes` `{score, feedback}` |
| `/student/api/topics/<id>/submission` | `POST` | `api_submit_topic_work` | `file`, `title` (Multipart Form) | Sube archivo de tarea a `/static/uploads/` y registra en `student_submissions` |
| `/student/api/topics/<id>/personalized-game` | `GET` | `api_personalized_game` | `topic_id` en URL | Reto lúdico personalizado generado para el alumno |
| `/student/api/topics/<id>/evaluation` | `GET` | `api_topic_evaluation` | `topic_id` en URL | **Examen formal de 15 preguntas** (solo preguntas en estado `PUBLISHED`) |
| `/student/api/topics/<id>/evaluation` | `POST` | `api_topic_evaluation` | `answers` (JSON) | Califica examen (escala 0-20), guarda en `student_assessment_attempts` e identifica temas a reforzar |
| `/student/api/assessments/attempts` | `GET` | `api_student_assessment_attempts` | Sesión activa | Historial cronológico de intentos formales en exámenes `{attempts}` |
| `/student/api/reinforcement-games` | `GET` | `api_get_reinforcement_games` | Sesión activa | Catálogo de los 3 juegos interactivos (Opción múltiple, V/F, Completar) |
| `/student/api/reinforcement-games/<id>` | `GET` | `api_get_reinforcement_game_detail`| `game_id` (1, 2 o 3) | Enunciado, opciones y metadatos del juego lúdico |
| `/student/api/reinforcement-games/<id>/play` | `POST` | `api_play_reinforcement_game` | `answer`, `time_spent` (JSON) | Evalúa respuesta, guarda intento en `student_game_attempts` y registra nota |
| `/student/api/reinforcement-games/recommendations` | `GET` | `api_get_reinforcement_game_recommendations` | Sesión activa | Detecta debilidades y prioriza qué juego debe practicar el alumno |
| `/student/api/reinforcement-games/attempts` | `GET` | `api_get_student_game_attempts` | Sesión activa | Historial de intentos y puntajes en juegos lúdicos |
| `/student/api/progress` | `GET` | `api_student_progress` | Sesión activa | Métricas de avance general, promedio y temas completados |
| `/student/api/recommendations` | `GET` | `api_student_recommendations` | Sesión activa | **Diagnóstico de los 4 pilares y plan adaptativo de 3 pasos (GOAL 6)** |
| `/student/api/risk-prediction` | `GET` | `api_student_risk_prediction` | Sesión activa | Predicción personalizada de riesgo del alumno con explicaciones |
| `/student/api/messages` | `GET` | `api_get_messages` | Sesión activa | Mensajes enviados por el profesor al alumno |
| `/student/api/messages/<id>/read` | `PUT` | `api_mark_message_read` | `message_id` en URL | Marca mensaje como leído |
| `/student/api/alerts` | `GET` | `api_get_alerts` | Sesión activa | Alertas y notificaciones para el alumno |
| `/student/api/alerts/<id>/read` | `PUT` | `api_mark_alert_read` | `alert_id` en URL | Marca alerta como leída |

---

### 4.6. `ai_controller.py`
- **Responsabilidad:** Consulta de estado del servicio Ollama y generación docente de retos lúdicos de tres niveles.
- **Dependencias:** `services.ai_service`, `services.db_service`.

| Ruta | Método | Función | Datos de Entrada | Respuesta / Salida |
|---|---|---|---|---|
| `/ai/status` | `GET` | `ollama_status` | Ninguno | Estado de Ollama (`running`, `model_available`, `host`, `model`) |
| `/ai/generar-juego/<topic_id>` | `POST` | `generar_juego_api` | `topic_id` en URL (Docente) | Invoca Ollama, genera juego de 3 niveles y preguntas, guarda en `topic_games` |
| `/ai/juego/<game_id>` | `GET` | `ver_juego_view` | `game_id` en URL | Renderiza vista `views/student_juegos.html` |
| `/ai/juego/<game_id>/json` | `GET` | `ver_juego_json` | `game_id` en URL | JSON del juego estructurado (`pares`, `niveles`, `instrucciones`) |

---

## 5. Análisis de la Capa de Servicios (Services Layer)

La capa de servicios contiene la lógica de negocio, integración con APIs externas, orquestación de bases de datos y algoritmos de Machine Learning.

| Servicio | Problema que Resuelve | Llamado por | Dependencias Directas | ¿Mezcla Responsabilidades? |
|---|---|---|---|---|
| [`db_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/db_service.py) | Abstracción de base de datos MySQL, consultas SQL, inserciones y fallback transparente a `mock_data.py` en modo offline. | Casi todos los controladores y servicios. | `mysql.connector`, `config.Config`, `services.mock_data`. | **Sí, severamente.** Es un archivo monolítico de 2,010 líneas y 83 funciones que mezcla esquema DDL, usuarios, temas, notas, exámenes, juegos, archivos y alertas. |
| [`ai_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ai_service.py) | Generación de planes curriculares, preguntas de comprensión estrictas sobre texto docente, juegos de 3 niveles con Ollama y fallback local. | `ai_controller.py`, `teacher_controller.py`, `teacher_assessment_controller.py`. | `ollama` (Client), `openai`, `config.Config`. | **Moderada.** Mezcla generación pedagógica por prompts con normalización de JSON, fallbacks estáticos y formateo de preguntas. |
| [`adaptive_recommendations_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/adaptive_recommendations_service.py) | **Motor Adaptativo (GOAL 6):** Unifica Notas + Evaluaciones + Juegos + Predicción ML y genera diagnósticos basados en evidencia real y planes de 3 acciones. | `student_controller.py`, `student_learning_service.py`. | `services.db_service`, `services.student_learning_service`. | **No.** Alta cohesión, función única bien delimitada. |
| [`reinforcement_games_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/reinforcement_games_service.py) | Lógica pedagógica de los 3 juegos lúdicos (Opción múltiple, V/F, Completar), evaluación lingüística y detección de debilidades. | `student_controller.py`. | `services.db_service`. | **No.** Diseñado con alta cohesión y responsabilidad única. |
| [`student_learning_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/student_learning_service.py) | Construcción de lecciones, evaluación formativa, cálculo de progreso general y cálculo de riesgo formativo para el estudiante. | `student_controller.py`. | `services.db_service`, `services.ml_service`, `services.ai_service`. | **Leve.** Orquesta múltiples componentes del alumno pero delega adecuadamente en submódulos. |
| [`teacher_assessment_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/teacher_assessment_service.py) | Generación formal de 15 preguntas por tema y calificación de evaluaciones. | `teacher_assessment_controller.py`, `student_controller.py`. | Ninguna externa (librerías estándar). | **No.** Responsabilidad única en generación y calificación de exámenes. |
| [`teacher_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/teacher_service.py) | Banco de preguntas predeterminado por tema y cálculo de métricas del dashboard docente. | `teacher_controller.py`. | Ninguna externa. | **No.** |
| [`teacher_reports_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/teacher_reports_service.py) | Conversión a escala vigesimal (0-20), rangos de fechas bimestrales y categorización de logro (Inicio, Proceso, Logrado, Destacado). | `teacher_reports_controller.py`, `teacher_controller.py`. | Ninguna externa. | **No.** Lógica de cálculo y consolidación analítica. |
| [`teacher_export_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/teacher_export_service.py) | Construcción de hojas de cálculo binarias Excel (`openpyxl`) con formato institucional y reportes en texto/PDF. | `teacher_export_controller.py`. | `openpyxl`, `services.teacher_reports_service`. | **No.** Enfocado exclusivamente en exportación de datos. |
| [`ml_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ml_service.py) | Fachada de compatibilidad hacia `services/ml/prediction_service.py` para controladores web. | `teacher_controller.py`, `student_learning_service.py`. | `services.ml.prediction_service`. | **No.** Fachada limpia (Facade pattern). |
| [`services/ml/prediction_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ml/prediction_service.py) | Orquestador de inferencia supervisada en caliente y traducción a explicabilidad pedagógica comprensible para el docente y alumno. | `ml_service.py`, `teacher_controller.py`. | `services.ml.feature_service`, `services.ml.model_registry`, `ml.pipeline.predictor`. | **No.** Alta cohesión en inferencia en producción. |
| [`services/ml/feature_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ml/feature_service.py) | Extracción de variables numéricas agregadas por estudiante con aislamiento temporal estricto anti-leakage. | `services.ml.prediction_service`. | `services.db_service`, `ml.pipeline.feature_builder`. | **No.** Responsabilidad única en construcción de vectores de entrada. |
| [`services/ml/model_registry.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ml/model_registry.py) | Registro de modelos, gestión del ciclo de vida y selector de fuente (`benchmark` vs `institutional`). | `services.ml.prediction_service`. | `config.Config`, `pathlib`. | **No.** Responsabilidad única en localización de artefactos serializados. |
| [`mock_data.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/mock_data.py) | Diccionarios y listas en memoria que replican el estado de una base de datos para demostración sin MySQL. | `db_service.py`, `auth_controller.py`. | Ninguna externa. | **No.** Datos estáticos simulados. |

---

## 6. Base de Datos Actual

### 6.1. Motor y Modo de Operación
- **Motor Primario:** **MySQL** (conectado a través de `mysql.connector`).
- **Modo Demostración Offline:** Cuando MySQL no está encendido o `USE_MOCK_DATA=true`, el sistema desvía todas las operaciones en memoria a `services/mock_data.py`.
- **Estrategia DDL:** Declarado en [`sql/schema.sql`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/sql/schema.sql), con comprobación condicional en `db_service.ensure_schema()`.

### 6.2. Diagrama Conceptual de Entidades Reales

```text
┌─────────────────────────────────────────────────────────────┐
│                           USERS                             │
│ (id, username, password_hash, role, email, phone, grade)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1:1 (si role = 'student')
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                          STUDENTS                           │
│ (id, user_id, first_name, last_name, grade, observations)   │
└──────┬───────────────────────┬───────────────────────┬──────┘
       │                       │                       │
       ▼ 1:N                   ▼ 1:N                   ▼ 1:N
┌──────────────┐      ┌─────────────────┐     ┌──────────────────┐
│STUDENT_NOTES │      │STUDENT_ASSESSM. │     │STUDENT_GAME_     │
│(score, perc, │      │ATTEMPTS         │     │ATTEMPTS          │
│wrong_answers,│      │(score, 12/15,   │     │(game_id, score,  │
│activity_type)│      │reinforce_topics)│     │is_correct, time) │
└──────▲───────┘      └────────▲────────┘     └────────▲─────────┘
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │ N:1
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                           TOPICS                            │
│ (id, title, description, grade, is_private, teacher_id)     │
└──────┬───────────────────────┬───────────────────────┬──────┘
       │                       │                       │
       ▼ 1:N                   ▼ 1:N                   ▼ 1:N
┌──────────────┐      ┌─────────────────┐     ┌──────────────────┐
│LEARNING_     │      │ASSESSMENT       │     │TOPIC_ACTIVITIES /│
│MATERIALS     │      │(status: APPROVED│     │TOPIC_GAMES       │
│(title,content│      │ PUBLISHED)      │     │(juegos 3 niveles,│
│ created_at)  │      │   └── QUESTIONS │     │ actividades)     │
└──────────────┘      └─────────────────┘     └──────────────────┘
```

### 6.3. Clasificación Exhaustiva de Tablas

#### Tablas Usadas Realmente por el Código
1. `users`: Cuentas de usuario, credenciales, correo y rol (`teacher`, `student`, `admin`).
2. `students`: Perfiles de alumnos vinculados a `users(id)` con grado escolar y observaciones.
3. `topics`: Temas curriculares creados por docentes o del plan de estudios.
4. `student_progress`: Registro de avance acumulado por tema para cada estudiante.
5. `ai_recommendations`: Registro histórico de sugerencias formativas generadas para el alumno.
6. `student_notes`: Almacén central de calificaciones en actividades, evaluaciones y juegos (escala vigesimal 0-20).
7. `learning_materials`: Materiales de lectura basados en texto publicados por los profesores.
8. `material_reviews`: Seguimiento de lectura y confirmación de revisión por parte del alumno.
9. `topic_activities`: Ejercicios prácticos asociados a los temas.
10. `topic_games`: Juegos educativos generados por IA (3 niveles) vinculados al tema.
11. `topic_evaluations`: Evaluaciones rápidas del tema.
12. `assessment`: Evaluaciones formales generadas con flujo de aprobación docente (`status`: `GENERATED`, `PENDING_REVIEW`, `APPROVED`, `PUBLISHED`).
13. `questions`: Preguntas individuales pertenecientes a un `assessment`, con distractores, respuesta correcta y estado de aprobación `approved`.
14. `student_assessment_attempts`: Intentos de evaluaciones formales con registro de tiempo, puntaje vigesimal, aciertos (`12/15`), porcentaje (`80%`) y lista JSON de `reinforce_topics`.
15. `student_game_attempts`: Intentos de los 3 juegos lúdicos interactivos de reforzamiento con registro de acierto, tiempo y respuesta enviada.
16. `topic_presentations`: Metadatos y rutas de archivos PowerPoint subidos por el profesor.
17. `student_submissions`: Tareas y archivos entregados por los alumnos para revisión docente.
18. `teacher_messages`: Mensajería unidireccional o bidireccional entre profesor y estudiante.
19. `student_academic_outcomes`: Registro de riesgo académico y estado de aprobación para importaciones históricas.
20. `alerts`: Consultada activamente por `db_service.py` (`fetch_alerts_for_user`, `mark_alert_as_read`), **aunque falta su DDL en `schema.sql`**.

#### Tablas Declaradas en `schema.sql` pero Sin Uso en el Código (Huérfanas / Duplicadas)
1. `grades`: Definida en líneas 75-84 de `schema.sql`. La aplicación nunca la consulta ni inserta datos; utiliza `student_notes`.
2. `teacher_topics`: Definida en línea 190 de `schema.sql`. Duplicada conceptualmente con `topics`.
3. `teacher_activities`: Definida en `schema.sql`. Duplicada con `topic_activities`.
4. `teacher_games`: Definida en `schema.sql`. Duplicada con `topic_games`.
5. `teacher_evaluations`: Definida en `schema.sql`. Duplicada con `topic_evaluations` y `assessment`.
6. `student_results`: Declarada en `schema.sql`. La función `fetch_student_results` en `db_service.py` fue redirigida a consultar `student_notes`.
7. `teacher_recommendations`: Declarada en `schema.sql`. El sistema utiliza `ai_recommendations`.

---

## 7. Frontend y Vistas (Views)

### 7.1. Sistema de Plantillas y Estructura Visual
- **Motor de Renderizado:** **Jinja2** integrado en Flask.
- **Framework CSS:** **Bootstrap 5.3** cargado por CDN (`bootstrap.bundle.min.js`), complementado con **Bootstrap Icons (1.11.0)** y estilos personalizados en `static/css/styles.css` y `static/css/student.css`.
- **Arquitectura de Interfaz:** Ambos portales (`teacher_dashboard.html` y `student_dashboard.html`) fueron construidos bajo un enfoque de **Dashboard SPA (Single Page Application)**:
  - Todo el contenido de las pestañas está pre-renderizado o cargado en secciones `<div id="section-..." class="section-panel">`.
  - La barra lateral (Sidebar) conmuta la clase `.active` entre paneles sin recargar la página.

### 7.2. Vistas Principales y Archivos JavaScript

#### 1. Portal del Profesor
- **Plantilla:** [`views/teacher_dashboard.html`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/views/teacher_dashboard.html) (70.8 KB)
- **JavaScript:** [`static/js/teacher.js`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/static/js/teacher.js) (126.8 KB)
- **Responsabilidades:**
  - Navegación entre secciones: Alumnos, Temas, Materiales, Generar IA, Evaluaciones y Reportes.
  - Creación y edición de temas curriculares mediante peticiones asíncronas `fetch()`.
  - Creación de material educativo en texto y generación de preguntas con IA.
  - Revisión pedagógica de evaluaciones (editar preguntas, aprobar preguntas individuales, aprobar examen completo y publicar para alumnos).
  - Consulta de predicciones de riesgo de alumnos mediante modal explicativo.
  - Subida de diapositivas `.pptx` y calificación de entregas estudiantiles.

#### 2. Portal del Alumno
- **Plantilla:** [`views/student_dashboard.html`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/views/student_dashboard.html) (56.6 KB)
- **JavaScript:** [`static/js/student.js`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/static/js/student.js) (107.6 KB)
- **Responsabilidades:**
  - Navegación entre secciones: Inicio/Temas, Mis Clases, Mis Materiales, Juegos, Evaluaciones, Recomendaciones, Mi Progreso.
  - Lectura interactiva de materiales del profesor y práctica de comprensión calificada por IA sin alucinaciones.
  - Examen formal de 15 preguntas con cronómetro de 20 minutos, calificación en vivo y reporte de temas a reforzar.
  - Área interactiva para los 3 juegos de reforzamiento (Opción múltiple, V/F, Completar espacios con banco de palabras).
  - Visualización del diagnóstico predictivo de aprendizaje y del plan adaptativo canónico de 3 pasos (📖 Leer material, 🎮 Juego, 📝 Evaluación).

### 7.3. Ejemplo del Flujo de Comunicación Frontend-Backend

```text
Alumno hace clic en "Finalizar y Calificar Evaluación"
                     │
                     ▼
                 student.js
(Captura evento click, recolecta respuestas marcadas en radio buttons)
                     │
                     ▼
      fetch('/student/api/topics/4/evaluation', {
         method: 'POST',
         headers: {'Content-Type': 'application/json'},
         body: JSON.stringify({ answers: {...} })
      })
                     │
                     ▼
         student_controller.py
(Valida sesión, califica respuestas con escala vigesimal 0-20,
 determina cantidad de aciertos ej: 12/15, porcentaje ej: 80%
 y calcula lista de reinforce_topics = ['Fracciones básicas'])
                     │
                     ▼
              db_service.py
(Inserta registro en student_assessment_attempts y sincroniza student_notes)
                     │
                     ▼
       Respuesta JSON al Navegador
{
  "success": true,
  "result": {
     "score": 16.0,
     "correct_answers": 12,
     "total_questions": 15,
     "percentage": 80.0,
     "reinforce_topics": ["Fracciones básicas"]
  }
}
                     │
                     ▼
                 student.js
1. Renderiza tarjeta de resultado con 12/15 y temas a reforzar.
2. Invoca automáticamente loadRecommendations().
                     │
                     ▼
      fetch('/student/api/recommendations')
                     │
                     ▼
    adaptive_recommendations_service.py
(Detecta las fallas del examen recién registrado, cruza notas,
 juegos y predicción ML, y actualiza el plan formativo)
                     │
                     ▼
                 student.js
(Actualiza en tiempo real las tarjetas de diagnóstico y los 3 botones:
 📖 Leer material: Fracciones básicas
 🎮 Juego: Comparar fracciones
 📝 Evaluación: Práctica corta)
```

---

## 8. Sistema Actual de Autenticación y Autorización

### 8.1. Mecanismo de Sesión y Almacenamiento
- **Mecanismo:** Sesiones de cliente firmadas criptográficamente por Flask en cookies HTTP (`session`).
- **Llave de Firma:** `Config.SECRET_KEY` (leída desde `.env` con fallback inseguro `'dev-secret-change-in-production'`).
- **Variables Guardadas en Sesión:**
  - `session['user']`: Nombre de usuario autenticado (`str`).
  - `session['user_role']`: Rol (`'teacher'`, `'student'`, `'admin'`).
  - `session['user_grade']`: Grado escolar (ej: `5` para primaria).
  - `session['student_id']`: ID numérico del registro de alumno (`int`), resuelto por `ensure_student_record_for_user()`.
  - `session['student_name']`: Nombre completo para encabezados y saludos.
  - `session['teacher_name']`: Nombre del docente.
  - `session['is_authenticated']`: Booleano de estado de sesión.

### 8.2. Roles Existentes y Protección de Rutas
Existen 3 roles definidos en los esquemas y datos mock:
1. `teacher`: Acceso exclusivo al prefijo `/teacher` y creación de contenidos.
2. `student`: Acceso exclusivo al prefijo `/student` y actividades de aprendizaje.
3. `admin`: Rol administrativo reconocido en esquemas, aunque sin controlador específico en la versión actual.

#### Funciones de Protección (Guards)
Cada controlador implementa una función interna de verificación que se invoca al inicio de cada endpoint:
- **`teacher_controller.py:_auth_check()`**:
  ```python
  if 'user' not in session or not session.get('is_authenticated'):
      return redirect(url_for('auth.login'))
  if session.get('user_role') != 'teacher':
      return redirect(url_for('student.student_home'))
  ```
- **`student_controller.py:_auth_check()`**:
  ```python
  if 'user' not in session or not session.get('is_authenticated'):
      return redirect(url_for('auth.login'))
  if session.get('user_role') != 'student':
      return redirect(url_for('teacher.teacher_home'))
  ```
- En endpoints de API (`/api/...`), la denegación retorna un código HTTP 401: `jsonify({'error': 'No autorizado'}), 401`.

---

## 9. Módulo de Machine Learning Clásico

El subsistema de Machine Learning fue auditado exhaustivamente, confirmando una implementación clásica rigurosa y libre de afirmaciones metodológicas incorrectas.

### 9.1. Arquitectura y Componentes
- **Ubicación del Código:** [`ml/pipeline/`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/ml/pipeline/) y [`services/ml/`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ml/).
- **Algoritmo Seleccionado:** **Random Forest Classifier** (`n_estimators=100`, `random_state=42`), seleccionado mediante comparación competitiva contra Regresión Logística y Decision Tree.
- **Dataset de Entrenamiento:**
  - **Activo:** Dataset benchmark UCI Student Performance (`ml/datasets/student-mat.csv`, 395 registros), mapeado a una escala vigesimal unificada (0-20).
  - **Institucional:** `ml/models/institutional/` se mantiene con estado transparente `not_trained`, indicando a tesistas y evaluadores que el modelo aún no ha sido reentrenado con datos históricos locales para evitar sesgos muestrales.
- **Comando Único de Entrenamiento:**
  ```bash
  python ml/run_pipeline.py --source benchmark
  ```
- **Métricas Oficiales Validadas en `ml/models/benchmark/metadata.json`:**
  - **Recall de Riesgo (Sensibilidad):** **90.48%** (prioridad clínica-educativa para no omitir alumnos en riesgo).
  - **Exactitud (Accuracy):** **91.15%**
  - **F1-Score:** **0.9024**
  - **ROC-AUC:** **0.9605**

### 9.2. Esquema Canónico de 18 Features (`features.json`)
Para garantizar paridad estricta entre entrenamiento e inferencia, el pipeline congela las siguientes 18 variables numéricas:
1. `total_attempts`: Total de interacciones formativas registradas.
2. `evaluation_count`: Cantidad de exámenes rendidos.
3. `activities_count`: Cantidad de actividades de aula realizadas.
4. `games_count`: Cantidad de retos lúdicos completados.
5. `average_score`: Promedio general en escala 0-20.
6. `average_evaluation_score`: Promedio específico en exámenes.
7. `average_activity_score`: Promedio específico en actividades.
8. `min_score`: Calificación más baja histórica.
9. `max_score`: Calificación más alta histórica.
10. `last_score`: Calificación del último evento registrado.
11. `score_std`: Desviación estándar de notas (estabilidad del rendimiento).
12. `score_trend`: Pendiente de evolución (mejora o declive temporal).
13. `total_correct_answers`: Sumatoria total de respuestas correctas.
14. `total_wrong_answers`: Sumatoria total de errores cometidos.
15. `accuracy_ratio`: Tasa de precisión global ($\frac{\text{correctas}}{\text{total}}$).
16. `average_time_spent_seconds`: Tiempo medio invertido por actividad.
17. `materials_reviewed_count`: Cantidad de lecturas revisadas por el alumno.
18. `submissions_count`: Cantidad de tareas entregadas.

### 9.3. Flujo de Inferencia y Explicabilidad Pedagógica

```text
               Estudiante Autenticado (ID: 1)
                             │
                             ▼
                 services/ml/feature_service.py
(Consulta student_notes, student_assessment_attempts y learning_materials
 con filtro cutoff_date anti-fuga temporal. Construye vector de 18 features)
                             │
                             ▼
                 services/ml/prediction_service.py
                             │
                             ▼
                 ml/pipeline/predictor.py
(Carga ml/models/benchmark/model.joblib, ejecuta predict_proba(X)
 y extrae importancia de variables mediante feature_importances_)
                             │
                             ▼
                Motor de Explicabilidad
(Traduce pesos numéricos a lenguaje natural pedagógico:
 - "Rendimiento promedio inferior al nivel esperado en evaluaciones (7.0/20)"
 - "Alta tasa de errores acumulados (4 preguntas falladas)")
                             │
                             ▼
                Salida JSON hacia Dashboard
{
  "risk_level": "Alto",
  "probability": 99.0,
  "factors": [
    "Promedio general bajo (7.0/20)",
    "Fallas frecuentes en evaluaciones de Fracciones básicas"
  ]
}
```

---

## 10. Módulo de Inteligencia Artificial Generativa

### 10.1. Infraestructura y Modelos
- **Ubicación del Servicio:** [`services/ai_service.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/services/ai_service.py)
- **Motor Local Primario:** **Ollama** vía cliente Python oficial (`from ollama import Client`).
- **Host y Puerto:** Configurado en `Config.OLLAMA_HOST` (por defecto `http://127.0.0.1:11434`).
- **Modelo Designado:** `llama3` (parametrizable en `Config.OLLAMA_MODEL`).
- **Motor Secundario (Opcional):** OpenAI (`gpt-3.5-turbo`) si `OPENAI_API_KEY` está presente.

### 10.2. Prompts y Tareas de Generación en el Sistema

1. **Generación Curricular de Temas (`generate_topic_content`):**
   - **Objetivo:** Generar un plan curricular completo de 4 bimestres, 8 unidades y 32 sesiones correlativas adaptadas al grado escolar.
   - **Formato de Salida:** Markdown estructurado con títulos, unidades y objetivos por sesión.
2. **Generación Estricta Basada en Material Docente (`generate_questions_from_teacher_material`):**
   - **Directriz Metodológica:** Cero alucinaciones. La IA tiene prohibido inventar contenido; solo formula preguntas y actividades a partir del texto que el profesor subió.
   - **Formato de Salida:** JSON estricto con fragmentos de referencia (`reference_fragment`) que justifican la respuesta correcta.
3. **Generación de Packs de Retos de 3 Niveles (`generate_topic_learning_pack`):**
   - **Nivel 1:** Relacionar conceptos (pares término-definición).
   - **Nivel 2:** Selección múltiple con 3 opciones distintas.
   - **Nivel 3:** Ordenamiento de pasos cronológicos del tema.
   - **Formato de Salida:** JSON que se persiste directamente en la tabla `topic_games`.

### 10.3. Mecanismos de Fallback y Resiliencia
Si Ollama no está en ejecución, se agota el tiempo de espera (timeout 180s) o devuelve un JSON malformado, `ai_service.py` intercepta la excepción y activa un generador local algorítmico (`_fallback_drag_drop_game`, `_fallback_quiz_questions`). La aplicación notifica al usuario con el indicador `source='local'` sin interrumpir el flujo del docente ni del estudiante.

---

## 11. Cobertura de Pruebas Automatizadas (Tests)

El sistema cuenta con una suite completa ejecutada con **pytest 9.1.1**.

### Resumen de Cobertura por Área

| Área / Módulo | Archivos de Prueba | Cantidad de Tests | Aspectos Críticos Cubiertos | Brechas / No Cubierto |
|---|---|:---:|---|---|
| **Machine Learning & Pipeline** | `test_ml_pipeline.py`, `test_ml_refactor.py` | **27 tests** | Carga de datos, validación de columnas, temporal cutoff anti-fuga, paridad de 18 features, inferencia determinística, métricas de validación y cambio entre datasets. | Pruebas de reentrenamiento continuo con millones de registros. |
| **Predicción del Estudiante** | `test_student_risk_prediction.py` | **8 tests** | Control de acceso por rol, aislamiento entre estudiantes, respuesta de modelo no disponible, factores explicativos y mensajes motivacionales. | Pruebas de estrés de inferencia concurrente. |
| **Recomendaciones Adaptativas** | `test_adaptive_recommendations.py` | **6 tests** | Unificación de los 4 pilares, 3 acciones canónicas (Leer, Juego, Examen), caso de fracciones, determinismo y actualización dinámica. | Pruebas de decaimiento temporal de notas a largo plazo. |
| **Aprobación Docente de Exámenes** | `test_assessment_approval_workflow.py` | **5 tests** | Ciclo de estados (`GENERATED` $\to$ `PENDING` $\to$ `APPROVED` $\to$ `PUBLISHED`), edición de preguntas, eliminación y bloqueo a alumnos. | Publicación masiva programada por fecha/hora. |
| **Evaluación Formal (15 Preguntas)** | `test_fifteen_questions_assessment.py` | **4 tests** | Examen de 15 preguntas, cálculo de nota vigesimal y porcentaje, guardado en `student_assessment_attempts` y temas a reforzar. | Preguntas abiertas con calificación semántica por NLP. |
| **Juegos Lúdicos de Reforzamiento** | `test_reinforcement_games.py` | **8 tests** | Los 3 juegos (Opción múltiple, V/F, Completar), tolerancia lingüística, guardado en `student_game_attempts` y recomendación por fallas. | Juegos multijugador en tiempo real con WebSockets. |
| **Materiales y Práctica IA** | `test_teacher_student_materials.py` | **6 tests** | Creación docente de material, lectura por alumno, generación de preguntas fundamentadas en texto y calificación de práctica. | Carga de PDFs pesados o imágenes con OCR. |
| **Reportes y Analíticas Docentes** | `test_teacher_reports.py`, `test_teacher_assessment_and_notes.py`, `test_teacher_export_and_student_analysis.py`, `test_teacher_module.py` | **15 tests** | Generación de libros Excel (.xlsx), documentos imprimibles, agrupamiento por estudiante, dashboard docente y promedios. | Exportación a formatos externos (Google Classroom, Moodle). |
| **Base de Datos & Esquema** | `test_db_service.py` | **2 tests** | Inyección de columnas faltantes y exclusión de temas privados entre grados. | Pruebas de concurrencia de transacciones ACID en MySQL. |
| **TOTAL** | **13 archivos** | **81 tests** | **100% pruebas aprobadas (`81 passed in 13.86s`)** | — |

---

## 12. Problemas Arquitectónicos Encontrados

Los hallazgos se clasifican estrictamente según su severidad sin haber aplicado alteraciones al código fuente.

### 12.1. Problemas Críticos (Seguridad e Integridad)

1. **Almacenamiento y Validación de Contraseñas en Texto Plano:**
   - En [`controllers/auth_controller.py`](file:///c:/Users/familia/Downloads/sistema%20IA/sistema%20IA/controllers/auth_controller.py#L25):
     ```python
     if user and password == user.get('password_hash'):
     ```
   - Las contraseñas en `mock_data.py` y en la tabla MySQL `users` se comparan como cadenas de texto plano sin sal (salt) ni funciones criptográficas (`bcrypt`, `argon2`, `pbkdf2_sha256`).
2. **Código Muerto en el Flujo de Autenticación de Dos Factores (2FA):**
   - En `controllers/auth_controller.py` (líneas 35-51), el código genera una redirección incondicional inmediata:
     ```python
     if session.get('user_role') == 'teacher':
         return redirect(url_for('teacher.teacher_home'))
     return redirect(url_for('student.student_home'))
     ```
   - Las instrucciones subsiguientes (generación de `two_step_code`, envío de SMS con Twilio, envío de Email y redirección a `auth.two_step`) son físicamente inalcanzables. Además, en `auth_controller.py:two_step`, la verificación de código se omite automáticamente si `stored_code` no está presente.
3. **Inconsistencia Crítica DDL en Tabla `alerts`:**
   - La tabla `alerts` es consultada formalmente por `db_service.py` (`fetch_alerts_for_user`, `get_unread_alerts_count`, `mark_alert_as_read`).
   - Sin embargo, **`alerts` no está definida en `sql/schema.sql`**. Al desplegar la aplicación en un servidor MySQL limpio ejecutando el script oficial, cualquier llamada a notificaciones generará un error de base de datos (`Table 'sistema_ia.alerts' doesn't exist`).
4. **Acoplamiento Directo al Dialecto MySQL en Capa de Datos:**
   - `services/db_service.py` ejecuta consultas con cadenas parametrizadas estilo `%s`, llamadas a `LAST_INSERT_ID()`, `AUTO_INCREMENT`, y captura excepciones `mysql.connector.Error`. No existe una capa de abstracción de datos (Repository o Unit of Work) ni un ORM, lo que impediría una transición inmediata hacia PostgreSQL sin reescribir consultas.

### 12.2. Problemas Importantes (Mantenibilidad y Escalabilidad)

1. **Monolito de Acceso a Datos (`db_service.py` con 2,010 líneas y 83 funciones):**
   - Centraliza todas las operaciones de persistencia del sistema en un solo archivo procedural, violando el principio de responsabilidad única (SRP).
2. **Duplicación Sistemática por Bipolo Mock/MySQL:**
   - Casi todas las funciones de `db_service.py` contienen bifurcaciones `if _use_mock():` que duplican la lógica entre manipulaciones de listas Python y sentencias SQL, aumentando el riesgo de desincronización funcional.
3. **Monolitos Frontend en JavaScript (`teacher.js` y `student.js`):**
   - Con más de 126 KB y 107 KB respectivamente, concentran lógica de negocio, construcción de HTML vía interpolación de strings (`innerHTML = ...`), gestión de estado, cronómetros y llamadas REST.
4. **Tablas Huérfanas y Redundantes en `sql/schema.sql`:**
   - Existen 7 tablas creadas en el DDL que no tienen ningún consumidor activo en el código de la aplicación: `teacher_topics`, `teacher_activities`, `teacher_games`, `teacher_evaluaciones`, `grades`, `student_results`, `teacher_recommendations`.
5. **Modelos de Dominio Abandonados (`models/`):**
   - `user_model.py`, `topic_model.py` y `teacher_model.py` existen en el proyecto pero nunca se importan; el código utiliza diccionarios genéricos (`dict`), perdiendo las ventajas del tipado estricto.
6. **Vistas HTML Huérfanas:**
   - `views/dashboard.html`, `views/student_topics.html` y `views/student_progress.html` son archivos obsoletos que fueron reemplazados por los dashboards integrados.

### 12.3. Problemas Menores (Organización y Código Limpio)

1. **Mezcla de Idiomas en Nombres de Recursos:**
   - Tablas en inglés (`students`, `assessment`, `student_game_attempts`) combinadas con tablas en español (`topic_evaluaciones`). Rutas en inglés (`/api/generate-topic`) y en español (`/api/generar-juego`).
2. **Archivos Legacy en el Árbol del Proyecto:**
   - La carpeta `legacy/` contiene una aplicación React inconclusa (`mi-app_vite_starter`) y una copia duplicada obsoleta del backend (`sistema_ia_v1_nested`), acumulando peso innecesario.
3. **Discrepancia entre `requirements.txt` y Entorno Virtual:**
   - `requirements.txt` lista únicamente 10 dependencias generales sin fijar versiones (pins), mientras el entorno virtual contiene 58 paquetes instalados.

---

## 13. Preparación para Nuevas Funcionalidades

### 13.1. Generación de Juegos con Ollama
- **Punto de Inserción Recomendado:**
  - Crear un servicio dedicado: `services/ai_game_generator_service.py` desacoplado de `ai_service.py`.
  - Conectar el endpoint en `teacher_assessment_controller.py` o en un nuevo `teacher_game_controller.py`.
- **Modificaciones de Base de Datos Necesarias:**
  - Vincular los juegos al material educativo agregando la columna `material_id INT NULL REFERENCES learning_materials(id)` en la tabla `topic_games`.
  - Incorporar una columna `status VARCHAR(20) DEFAULT 'PENDING_REVIEW'` y `approved BOOLEAN DEFAULT FALSE` en `topic_games`, replicando el exitoso flujo de validación docente del GOAL 3 para evitar que juegos generados sin revisión se publiquen automáticamente a los alumnos.

### 13.2. Migración a PostgreSQL y Nueva Autenticación
- **Impacto de la Migración:**
  - Reemplazar el conector `mysql-connector-python` por `psycopg2-binary` o `asyncpg`, o preferiblemente introducir **SQLAlchemy 2.0**.
  - Adaptar tipos de datos del esquema DDL:
    - `INT AUTO_INCREMENT` $\to$ `BIGINT GENERATED ALWAYS AS IDENTITY` o `SERIAL`.
    - `TINYINT(1)` $\to$ `BOOLEAN`.
    - `DATETIME` $\to$ `TIMESTAMPTZ`.
    - `JSON` $\to$ `JSONB` (permitiendo indexación GIN para búsquedas eficientes en `reinforce_topics` y `answers`).
  - Actualizar el parseo de variables de entorno en `config.py` para aceptar una URI estándar: `DATABASE_URL=postgresql://usuario:password@localhost:5432/sistema_ia`.
- **Implementación de Nueva Autenticación:**
  - Adoptar `werkzeug.security.generate_password_hash` y `check_password_hash` con algoritmo `scrypt` o `pbkdf2:sha256`.
  - Implementar tokens de sesión seguros o JWT con expiración estricta.
  - Eliminar el código muerto de 2FA o implementarlo mediante contraseñas de un solo uso basadas en tiempo (TOTP estándar con `pyotp` y códigos QR en pantalla) para prescindir de servicios SMS externos.

### 13.3. Sistema Educativo Adaptativo
- **Piezas ya Existentes y Funcionales:**
  - ✅ **Evaluaciones formales con desglose de debilidades:** `student_assessment_attempts` calcula y almacena la lista de `reinforce_topics`.
  - ✅ **Juegos de práctica lúdica:** 3 modalidades operativas con persistencia en `student_game_attempts`.
  - ✅ **Calificaciones normalizadas:** `student_notes` unifica notas en escala 0-20.
  - ✅ **Modelo predictivo ML:** Clasificador Random Forest en caliente con métricas validadas y explicabilidad pedagógica.
  - ✅ **Recomendaciones personalizadas unificadas:** `build_adaptive_recommendations()` ya entrega la terna canónica (📖 Leer material $\to$ 🎮 Juego $\to$ 📝 Evaluación) basada en datos reales.
- **Evolución Arquitectónica Recomendada:**
  - Modelar un **Grafo de Conocimiento Curricular (Knowledge Graph)** que formalice las relaciones de prerrequisito entre temas (ejemplo: *Multiplicación* es prerrequisito estricto de *División* y de *Fracciones básicas*).
  - Algoritmo de dificultad dinámica (Teoría de Respuesta al Ítem - IRT): Ajustar el nivel del juego según la tasa de aciertos y tiempo de respuesta del estudiante.

---

## 14. Recomendaciones Priorizadas para Siguientes GOALs

Con base en la auditoría realizada, se establece la siguiente hoja de ruta arquitectónica ordenada por criticidad y valor técnico:

1. **Prioridad 1 — Seguridad de Autenticación y Criptografía:**
   - Migrar contraseñas a hashes seguros (`generate_password_hash`).
   - Limpiar el código muerto en `auth_controller.py`.
   - Establecer `SECRET_KEY` aleatoria obligatoria en producción.
2. **Prioridad 2 — Regularización del Esquema SQL:**
   - Agregar el DDL de la tabla `alerts` a `sql/schema.sql`.
   - Depurar del DDL las 7 tablas huérfanas que no se utilizan para evitar confusiones en futuros desarrolladores.
   - Congelar las versiones de librerías en `requirements.txt`.
3. **Prioridad 3 — Desacoplamiento de la Capa de Datos para PostgreSQL:**
   - Modularizar `services/db_service.py` en repositorios por dominio (`user_repository.py`, `student_repository.py`, `assessment_repository.py`).
   - Introducir un adaptador de conexión compatible con PostgreSQL (`DATABASE_URL`).
4. **Prioridad 4 — Modularización del Frontend:**
   - Descomponer `student.js` y `teacher.js` en módulos independientes (navegación, evaluaciones, juegos, adaptativo) utilizando módulos estándar de JavaScript (`<script type="module">`).
5. **Prioridad 5 — Limpieza de Componentes Legacy:**
   - Archivar o remover de forma segura los archivos redundantes en `legacy/` y las plantillas HTML huérfanas identificadas.

---
*Fin de la Auditoría Técnica de Arquitectura.*
