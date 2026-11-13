# Arquitectura del Sistema de Machine Learning Escolar

## 1. Visión General de la Arquitectura

El subsistema de Machine Learning de **Sistema IA** está diseñado bajo los principios de modularidad, reproducibilidad, explicabilidad y desacoplamiento estricto entre los datos de investigación/benchmark y los datos institucionales del colegio.

El objetivo central es proporcionar predicción temprana de riesgo académico antes de la culminación del periodo lectivo, permitiendo la intervención pedagógica oportuna sin comprometer la privacidad del estudiante.

```
+-----------------------------------------------------------------------------------+
|                              Capa de Presentación                                 |
|   Dashboard Docente (HTML/Jinja2/Bootstrap) <---> teacher.js (Tarjeta Predictiva) |
+------------------------------------------^----------------------------------------+
                                           | HTTP JSON REST
+------------------------------------------v----------------------------------------+
|                               Capa de Control Flask                               |
|   GET  /teacher/api/students/<id>/risk   |   POST /teacher/api/predict-student    |
+------------------------------------------^----------------------------------------+
                                           | Inferencia
+------------------------------------------v----------------------------------------+
|                         Capa de Servicios de Inferencia                           |
|       RiskPredictionService <-------------> AcademicRiskPredictor (Pipeline)     |
|              |                                        ^                           |
|              v                                        |                           |
|       ModelRegistry (Singleton / Cache) --------------+                           |
|       (Resuelve ML_DATASET_SOURCE: benchmark vs institutional)                    |
+-----------------------------------------------------------------------------------+
                                           | Carga de Artefactos
+------------------------------------------v----------------------------------------+
|                          Capa de Artefactos y Modelos                             |
|   ml/models/benchmark/ (model.joblib, metadata.json, training_results.json)       |
|   ml/models/institutional/ (model.joblib, metadata.json)                          |
+-----------------------------------------------------------------------------------+
                                           ^ Entrenamiento
+------------------------------------------|----------------------------------------+
|                          Capa de Pipeline Reproducible                            |
|   data_loader.py ---> feature_builder.py ---> preprocessing.py ---> trainer.py    |
|                             |                      |                              |
|                             v                      v                              |
|                       features.json        evaluator.py (ROC-AUC, Recall, Matriz) |
+-----------------------------------------------------------------------------------+
```

---

## 2. Componentes del Pipeline (`ml/pipeline/`)

### 2.1. `data_loader.py` (Ingesta y Validación)
* Carga de archivos CSV crudos e institucionales.
* Validación obligatoria de columnas: `student_code`, `academic_year`, `period`, `subject`, `event_date`, `activity_type`, `score`, `final_status`.
* Validación de tipos de datos y rangos vigesimales ($0.0 \le \text{nota} \le 20.0$).
* Validación de exclusión de identificadores personales en la matriz $X$.

### 2.2. `preprocessing.py` (Transformadores scikit-learn)
* Construcción de objetos `Pipeline` con `SimpleImputer(strategy='median')` y `StandardScaler()`.
* **Garantía metodológica**: Cero preprocesamiento manual fuera de `sklearn.pipeline.Pipeline`, evitando data leakage.

### 2.3. `feature_builder.py` (Ingeniería de Variables y Anti-Leakage)
* Extrae las 18 variables predictivas canónicas agregadas a partir de eventos formativos.
* Aplica filtro temporal estricto mediante `cutoff_date`: solo los eventos con fecha menor o igual al corte participan en el cálculo.
* Serializa `features.json` para garantizar coherencia dimensional entre entrenamiento e inferencia.

### 2.4. `trainer.py` (Entrenamiento Multimodelo y Selección)
* Entrena y compara 4 familias supervisadas:
  1. `LogisticRegression`
  2. `DecisionTreeClassifier`
  3. `RandomForestClassifier`
  4. `GradientBoostingClassifier`
* Aplica validación cruzada temporal (Train en cohortes pasadas, Test en out-of-time holdout) o `GroupShuffleSplit`.
* Guarda `training_results.json`, `validation_metadata.json`, `metadata.json` y el modelo ganador en `model.joblib`.
* **Criterio de selección automática**: Prioridad 1: Recall de clase de riesgo ($y=1$); Prioridad 2: F1-Score ($y=1$); Prioridad 3: ROC-AUC.

### 2.5. `evaluator.py` (Métricas y Diagnóstico)
* Calcula Exactitud, Precisión, Recall, F1-Score, Matriz de Confusión y ROC-AUC.
* Extrae la importancia relativa de variables para los algoritmos ganadores.

### 2.6. `predictor.py` (Motor de Inferencia y Explicabilidad)
* Encapsula la carga del artefacto `.joblib` y traduce la salida numérica del clasificador en explicaciones en lenguaje natural para los docentes (`main_factors`) y descriptores técnicos para APIs (`explanation`).

### 2.7. `ml/run_pipeline.py` (Orquestador de Comando Único)
* Script ejecutor de nivel superior que automatiza los 4 pasos del ciclo de vida en una sola instrucción:
  1. Ingesta y validación de calidad de datos (`data_loader`).
  2. Extracción anti-leakage y serialización de `features.json` (`feature_builder`).
  3. Entrenamiento y comparación multimodelo con selección del ganador (`trainer`).
  4. Diagnóstico de inferencia y prueba de explicabilidad (`predictor`).
* Permite alternar entre el entorno de benchmark y el institucional mediante `--source {benchmark,institutional}` sin necesidad de comandos manuales concatenados.

---

## 3. Separación de Fuentes de Datos (`ML_DATASET_SOURCE`)

El sistema implementa dos entornos desacoplados gobernados por la variable de configuración `ML_DATASET_SOURCE`:

| Característica | Entorno `benchmark` | Entorno `institutional` |
| :--- | :--- | :--- |
| **Propósito** | Demostración técnica y experimental | Producción escolar e investigación final |
| **Dataset Crudo** | `ml/datasets/benchmark/raw/` | `ml/datasets/institutional/raw/` |
| **Dataset Procesado** | `ml/datasets/benchmark/processed/` | `ml/datasets/institutional/processed/` |
| **Modelos Serializados** | `ml/models/benchmark/` | `ml/models/institutional/` |
| **Origen de Datos** | UCI Student Performance (Cortez & Silva) | Calificaciones históricas del colegio |
| **Estado Inicial** | Modelo entrenado y disponible | `MODEL_NOT_AVAILABLE` (esperando datos) |

La conmutación se realiza sin alterar código, únicamente modificando `.env`:
```env
ML_DATASET_SOURCE=benchmark      # Para pruebas técnicas y demostración
# o
ML_DATASET_SOURCE=institutional  # Para producción con datos del colegio
```

---

## 4. Contratos de API REST

### Endpoint Institucional de Riesgo por Alumno
* **Ruta**: `GET /teacher/api/students/<int:student_id>/risk`
* **Parámetros Query**: `cutoff_date` (opcional, formato `YYYY-MM-DD`)
* **Autenticación**: Sesión de docente requerida
* **Respuesta Exitosa (HTTP 200)**:
```json
{
  "student_id": 15,
  "student_name": "Juan Pérez",
  "prediction": {
    "risk_level": "HIGH",
    "probability": 0.9875
  },
  "model": {
    "name": "RandomForest",
    "version": "v1_20260917",
    "dataset": "benchmark"
  },
  "explanation": [
    "low evaluation performance",
    "recent grades downward trend",
    "last recorded score in failing range"
  ],
  "main_factors": [
    "Bajo rendimiento en evaluaciones formativas (promedio menor a 11)",
    "Tendencia descendente en las últimas calificaciones",
    "Última calificación registrada en nivel reprobatorio (5.5/20)"
  ],
  "risk_level": "Alto"
}
```

---

## 5. Principios de Seguridad y Privacidad
1. **Anonimización Estricta**: `student_code`, `student_id`, nombres, DNI y correos son excluidos por aserción matemática de la matriz de características $X$.
2. **Anti-Leakage**: La fecha de corte temporal (`cutoff_date`) aísla de manera estricta los eventos formativos del target final de periodo, impidiendo que calificaciones futuras influyan en la predicción.
