# Aula de computación para primaria

Producto de tesis para materiales, juegos de entrenamiento, prácticas y exámenes. Aplicación publicada en https://aula-computacion-tesis.onrender.com con Render Free y PostgreSQL en Neon. El servicio gratuito puede suspenderse y tardar en arrancar.

## Reglas actuales

Los ocho juegos no alteran notas. El docente genera desde PPT o texto, edita con formularios, revisa y publica. El alumno responde con contenido guardado y no espera llamadas a IA.

La libreta usa tareas, participación y libro con 10 % cada uno, práctica 1 y práctica 2 con 10 % cada una y examen con 50 %. El docente registra solo los tres primeros; los otros provienen de evaluaciones explícitamente vinculadas. Una nota ausente deja el promedio pendiente. Prácticas repetibles; examen con un intento de treinta minutos y reapertura docente. El cierre congela notas y pesos y requiere calendario confirmado.

El historial AD/A/B/C se conserva sin conversión numérica. Un único bimestre no permite validar predicción futura. El modelo benchmark es una referencia técnica, sin validación institucional del colegio.

## Desarrollo local

Python 3.12 y PostgreSQL. Copiar `.env.example` a `.env` y configurar DATABASE_URL, SECRET_KEY, AI_PROVIDER y GROQ_API_KEY. No publicar claves.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.\.venv\Scripts\python.exe scripts/setup_db.py
.\.venv\Scripts\python.exe app.py
```

El instalador aplica migraciones repetibles y conserva datos; no carga padrón por defecto. Las cuentas ficticias se crean expresamente con scripts/seed_demo.py. USE_MOCK_DATA=true sirve para pruebas, no para persistencia escolar. No se incluyen contraseñas reales en la documentación pública.

## Ubicación del código

| Función | Archivos principales |
| --- | --- |
| HTTP y autorización | controllers/ y app.py |
| Reglas y persistencia | services/ y sql/migrations/postgresql/ |
| Pantallas | views/ y static/js/ |
| Generación desde PPT | material_extractor_service.py y ai_game_generator_service.py |
| Edición visual | static/js/teacher_game_editor.js |
| Intentos y calificación | services/learning_attempt_service.py |
| Libreta y cierre | bimester_grade_service.py y academic_closure_service.py |
| Historial literal | services/literal_history_service.py |
| Inferencia ML | ml/pipeline/predictor.py y services/ml/prediction_service.py |
| Entrenamiento | ml/run_pipeline.py y ml/pipeline/trainer.py |

La arquitectura técnica es un monolito modular Flask con Blueprints. TOGAF organiza su arquitectura y gobierno; no es una dependencia instalable.

## Verificación y datos

Instalar pytest y ejecutar `python -m pytest tests -q`. Las pruebas ordinarias usan datos ficticios. Las integraciones PostgreSQL requieren TEST_DATABASE_URL y crean esquemas aislados.

`python ml/run_pipeline.py --source benchmark` vuelve a entrenar modelos de referencia; no entrena con registros del colegio. El importador `scripts/import_literal_gradebook.py --input C:\ruta\registro.xlsx` valida sin escribir; solo --apply guarda las coincidencias verificadas. No convierte AD/A/B/C a números.

## Documentación vigente

- [Arquitectura y TOGAF 9.2](docs/arquitectura-togaf-9-2.md)
- [Libreta bimestral](docs/libreta-bimestral.md)
- [Despliegue gratuito](docs/despliegue-gratuito.md)
- [Evidencia y límites](docs/validacion-cambios-nube.md)
- [Piloto humano](docs/protocolo-piloto.md)

Las guías históricas con Ollama o acceso local describen versiones anteriores. Groq es el proveedor configurado y NVIDIA una alternativa explícita; Ollama local no es obligatorio. La validación vigente no sustituye la evidencia original de pretest y postest de la tesis.
