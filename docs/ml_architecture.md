# Arquitectura del subsistema de Machine Learning

El sistema separa generación de contenido y predicción tabular. Groq genera borradores docentes desde material; scikit-learn estima un resultado usando un artefacto entrenado. Ninguno sustituye la evaluación del docente.

## Recorrido del código

| Paso | Archivo | Responsabilidad |
| --- | --- | --- |
| Petición docente | controllers/teacher_controller.py | Riesgo del alumno y ficha del modelo |
| Petición del alumno | controllers/student_controller.py | Estado del propio alumno |
| Adaptación de respuesta | services/ml_service.py | Conserva estados y exige alumno identificado |
| Lectura de historial | services/ml/feature_service.py | Consulta PostgreSQL y delega la extracción |
| Extracción compartida | ml/pipeline/feature_builder.py | Dieciocho variables con corte y validación |
| Registro | services/ml/model_registry.py | Selecciona fuente y carga artefacto en memoria |
| Inferencia | services/ml/prediction_service.py y ml/pipeline/predictor.py | Probabilidad, clase, estados y avisos |
| Preparación UCI | ml/scripts/download_and_prepare_benchmark.py | Un curso oficial y procedencia verificable |
| Entrenamiento | ml/run_pipeline.py y ml/pipeline/trainer.py | Validación interna, selección y prueba separada |

El artefacto activo de benchmark está en ml/models/benchmark/. El institucional está separado y no tiene un modelo validado con los registros disponibles. La ficha lee el algoritmo y las métricas del artefacto, sin nombres ni porcentajes de respaldo inventados. La tabla de candidatos corresponde a validación interna; el resultado final se conserva separado en test_metrics.

## Contratos y límites

Los identificadores sirven para consultar y separar registros; no son entradas predictivas. No se entrena dentro de una petición del navegador. Un error de consulta, falta de historial, modelo ausente o fallo de inferencia conserva su estado explícito. No se sustituye con una regla de progreso ni con 50 %.

El benchmark usa división por alumno, sin afirmar cohortes históricas. La partición temporal institucional requiere periodos reales suficientes. El registro literal AD/A/B/C conserva su propio esquema y no se fuerza dentro de un importador numérico.

Consultar [metodología y resultados](ml_methodology.md) y [arquitectura con TOGAF](arquitectura-togaf-9-2.md). La separación modular permite ubicar y comprobar una función; no demuestra por sí sola validez científica o adopción institucional del marco.
