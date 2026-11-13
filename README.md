# Sistema Inteligente Educativo

Para publicar la versión de sustentación sin Ollama, consulta [el despliegue gratuito con Render, PostgreSQL y Groq](docs/despliegue-gratuito.md). La configuración está en `render.yaml`; usa `requirements-runtime.txt` para el servidor. También se documenta la [arquitectura de negocio propuesta](docs/arquitectura-negocio-propuesta.md).

Plataforma integral desarrollada en Python con Flask para la gestión académica escolar, soporte pedagógico docente y acompañamiento formativo del estudiante. El sistema cuenta con dos subsistemas inteligentes claramente diferenciados:

1. **Inteligencia Artificial Generativa (LLM)**: Integrada mediante Ollama y OpenAI para la generación dinámica de planes de clase, rúbricas pedagógicas, actividades interactivas, juegos educativos y resúmenes formativos.
2. **Machine Learning Supervisado (Predictivo)**: Módulo reproducible de predicción temprana de riesgo académico escolar basado en `scikit-learn`. Cuenta con un benchmark internacional de validación técnica (*Cortez & Silva, 2008*), motor de explicabilidad pedagógica (XAI) y arquitectura desacoplada lista para entrenar con datos históricos propios del colegio.

---

## 🚀 Puesta en Marcha en 1 Clic (Para Evaluación y Jurado)

Para usuarios no técnicos, docentes o miembros del jurado evaluador, el sistema cuenta con un lanzador directo de Windows:

1. **Doble clic** en el archivo:
   ```text
   iniciar_sistema.bat
   ```
2. El servidor iniciará automáticamente (detectando PostgreSQL o activando modo demostración si no hay PostgreSQL local) y abrirá el navegador en:  
   `http://127.0.0.1:5000/login`
3. En la pantalla de login, use los botones de acceso directo:
   * **`[ Ingresar como Profesor (Demo) ]`** (credenciales `profesor1` / `Admin123`).
   * **`[ Ingresar como Alumno (Demo) ]`** (credenciales `alumno1` / `Alumno123`).

## Base de datos PostgreSQL

La única base de datos oficial es PostgreSQL 18 o posterior. Copia `.env.example` a `.env` y configura `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`. Luego ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\setup_db.py
.\.venv\Scripts\python.exe scripts\test_db.py
.\.venv\Scripts\python.exe app.py
```

El instalador crea la base, aplica el DDL de [`sql/postgresql/ddl.sql`](sql/postgresql/ddl.sql), ejecuta las migraciones de [`sql/migrations/postgresql/`](sql/migrations/postgresql/) y carga [`sql/postgresql/seed.sql`](sql/postgresql/seed.sql). Puedes volver a ejecutar `scripts/setup_db.py` para actualizar una base existente; las migraciones son repetibles. Los usuarios seed usan hashes scrypt; las credenciales de desarrollo son `admin` / `Admin123`, `profesor1` / `Admin123` y `alumno1` / `Alumno123`.

Para trasladar una instalación histórica de MySQL una única vez, configura las variables `MYSQL_SOURCE_HOST`, `MYSQL_SOURCE_PORT`, `MYSQL_SOURCE_USER`, `MYSQL_SOURCE_PASSWORD` y `MYSQL_SOURCE_DB`, instala de forma temporal `mysql-connector-python` y ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\mysql_to_postgres.py
```

Ese script es exclusivamente de importación; la aplicación no usa MySQL como fallback.

---

## 🔍 Comando de Auditoría del Sistema (`verify_system.py`)

Para comprobar en 3 segundos que todos los componentes (Base de Datos, Modelo ML, Pipeline de Entrenamiento y Rutas Web) están 100% operativos:

```powershell
python verify_system.py
```

---

## 1. Documentación para Tesis y Manuales de Uso

El proyecto cuenta con documentación académica y técnica completa ubicada en el directorio [`docs/`](docs/):

* ⏱️ **[Guía Rápida de 5 Pasos para Demostración](docs/guia_rapida_demostracion.md)**: Manual ultra conciso: 1. Iniciar, 2. Login docente, 3. Seleccionar alumno, 4. Ver predicción, 5. Interpretar factores.
* 🎓 **[Guía Completa de Demostración para Jurado y Tesista](docs/guia_demostracion_jurado.md)**: Guion de 5 minutos, clics exactos, qué decir en cada pantalla y respuestas a preguntas del jurado.
* 🖥️ **Pantalla de Estado del Modelo ML**: Disponible en la aplicación web en [`/teacher/ml-status`](http://127.0.0.1:5000/teacher/ml-status) (muestra algoritmo, fuente benchmark, estado y advertencia de uso institucional).
* 📘 **[Metodología y Fundamentación Científica](docs/ml_methodology.md)**: Justificación del dataset de benchmark, formulación matemática de la escala vigesimal (0-20), comparación de algoritmos y matriz de costos pedagógicos.
* 🏛️ **[Arquitectura de Machine Learning](docs/ml_architecture.md)**: Diagrama de capas, flujos de datos, aislamiento temporal anti-leakage y contratos de API REST.
* 🎓 **[Guía de Defensa de Tesis](docs/thesis_defense_guide.md)**: Preguntas críticas del jurado evaluador, respuestas metodológicas sólidas y protocolo de defensa.
* 👥 **[Guía de Pruebas para Usuarios No Técnicos](docs/user_testing_guide.md)**: Manual detallado para docentes y directores con casos de prueba paso a paso.

---

## 2. Estructura del Proyecto

```text
sistema IA/
├── app.py                      # Punto de entrada de la aplicación Flask
├── config.py                   # Configuración central (ML_DATASET_SOURCE, BD, credenciales)
├── controllers/                # Controladores HTTP y Blueprints REST
│   ├── auth_controller.py
│   ├── student_controller.py
│   ├── teacher_controller.py   # Incluye GET /teacher/api/students/<id>/risk
│   └── teacher_reports_controller.py
├── views/                      # Plantillas Jinja2 / HTML5 (Dashboard docente)
├── static/                     # Assets CSS, JavaScript (teacher.js)
├── services/                   # Lógica de negocio desacoplada
│   ├── db_service.py           # Conexión PostgreSQL y persistencia
│   ├── grade_service.py        # Conversión canónica a escala vigesimal (0-20)
│   ├── ai_service.py           # IA Generativa (Ollama / OpenAI)
│   ├── ml_service.py           # Fachada de integración
│   └── ml/                     # Servicios de inferencia y registro
│       ├── model_registry.py   # Soporte dinámico benchmark vs institucional
│       ├── feature_service.py  # Extracción de variables con cutoff_date
│       └── prediction_service.py # Inferencia y explicabilidad
├── ml/                         # Subsistema de Machine Learning
│   ├── run_pipeline.py         # 🚀 COMANDO ÚNICO DE EJECUCIÓN DEL PIPELINE
│   ├── pipeline/               # Paquete modular de Machine Learning
│   │   ├── data_loader.py      # Carga y validación estricta de CSV
│   │   ├── preprocessing.py    # Pipeline puro scikit-learn
│   │   ├── feature_builder.py  # 18 variables canónicas anti-leakage
│   │   ├── trainer.py          # Comparación de 4 familias supervisadas
│   │   ├── evaluator.py        # Métricas, ROC-AUC e importancia de variables
│   │   └── predictor.py        # Motor de inferencia y explicabilidad
│   ├── datasets/
│   │   ├── benchmark/          # Datos públicos internacionales (UCI Cortez & Silva)
│   │   └── institutional/      # Datos históricos propios de la institución
│   ├── models/
│   │   ├── benchmark/          # Modelo ganador, training_results.json, metadata.json
│   │   └── institutional/      # Artefactos del colegio
│   └── scripts/
│       ├── import_school_dataset.py # Validador e importador del colegio
│       ├── build_dataset.py
│       └── evaluate.py
├── docs/                       # Documentación formal para tesis y guías de uso
└── tests/                      # Suite de pruebas automatizadas con pytest
```

---

## 3. Comando Único de Machine Learning (`run_pipeline.py`)

Para ejecutar de manera 100% reproducible el ciclo de vida completo de Machine Learning (validación de datos, extracción anti-leakage, comparación multialgorítmica, selección del ganador y diagnóstico de explicabilidad), basta con ejecutar un único comando:

```powershell
.\.venv\Scripts\python.exe ml/run_pipeline.py
```

### Opciones Soportadas:
```powershell
# Ejecutar en modo institucional (datos propios del colegio):
.\.venv\Scripts\python.exe ml/run_pipeline.py --source institutional

# Ejecutar con partición agrupada por estudiante (GroupSplit):
.\.venv\Scripts\python.exe ml/run_pipeline.py --split-strategy group

# Especificar fecha de corte formativa personalizada:
.\.venv\Scripts\python.exe ml/run_pipeline.py --cutoff-date 2024-05-15
```

---

## 4. Diferenciación Técnica: IA Generativa vs. ML Supervisado

| Criterio | IA Generativa (LLM) | Machine Learning Supervisado |
| :--- | :--- | :--- |
| **Tecnología** | Ollama (Llama 3 / Mistral) / OpenAI | Scikit-learn (LogisticRegression, DecisionTree, RandomForest, GradientBoosting) |
| **Propósito** | Creación de contenido didáctico, quizzes, fichas y rúbricas. | Predicción temprana de riesgo académico escolar (Bajo / Medio / Alto). |
| **Explicabilidad** | Respuestas en lenguaje natural estructurado. | Factores determinantes basados en importancia de características (`main_factors`). |
| **Garantía Temporal** | Generación interactiva en tiempo real. | Aislamiento temporal estricto (`cutoff_date`) sin contaminación retrospectiva. |

---

## 5. Ejecución de la Suite de Pruebas

Para verificar la integridad del código, el aislamiento temporal, la ausencia de fuga de identificadores y los endpoints REST:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

> **Resultado actual**: **44 de 44 pruebas aprobadas (100% verde)**.
