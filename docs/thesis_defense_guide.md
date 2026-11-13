# Guía de Defensa de Tesis: Preguntas Críticas del Jurado y Respuestas Metodológicas

Este documento proporciona al tesista los argumentos teóricos, metodológicos, matemáticos y legales para sustentar con solidez el subsistema de Machine Learning ante el Jurado de Tesis.

---

## 1. Preguntas Frecuentes del Jurado Evaluador

### Pregunta 1: "¿Por qué se utilizó un dataset de Portugal (UCI) y no directamente los datos del colegio desde el primer día?"
> **Respuesta Clave**:
> *"Durante la fase de auditoría diagnóstica de los registros proporcionados inicialmente por la institución escolar, se identificó que los archivos presentaban limitaciones insalvables para el entrenamiento supervisado:*
> 1. *Target monoclase sin casos de desaprobación (0% de estudiantes reprobados).*
> 2. *Muestra insuficiente que no alcanzaba la potencia estadística mínima.*
> 3. *Desplazamientos sistemáticos de calificaciones entre grados que evidenciaban alteración previa de los datos.*
> 
> *Fabricar datos sintéticos o falsificar registros hubiera constituido una **violación a la integridad ética de la investigación científica**. Por ello, se recurrió al benchmark internacional canónico de **Cortez & Silva (2008)**, el cual comparte idéntica **escala vigesimal oficial (0 a 20)** que el sistema educativo peruano.*
> 
> *El dataset benchmark permitió demostrar de forma rigurosa la viabilidad técnica, algorítmica y reproducible del pipeline. La arquitectura queda formalmente preparada con el **modo institucional (`ML_DATASET_SOURCE=institutional`)** y un script importador validado para que, en cuanto el colegio entregue su histórico consolidado, se reentrene el modelo definitivo mediante un único comando (`python ml/run_pipeline.py --source institutional`) sin modificar una sola línea de código."*

---

### Pregunta 2: "¿Cómo garantiza técnicamente que no exista fuga de datos (*Data Leakage*)?"
> **Respuesta Clave**:
> *"El pipeline implementa una barrera temporal estricta mediante el parámetro `cutoff_date` (fecha de corte formativa):*
> 1. *La matriz de características $X$ se calcula **única y exclusivamente** con eventos (tareas, exámenes formativos, participaciones) ocurridos con fecha $\le \text{cutoff\_date}$.*
> 2. *La variable objetivo ($y$) se determina a partir de la calificación sumativa oficial final ($G_3$) ocurrida al cierre del periodo lectivo.*
> 3. *Ninguna calificación posterior a la fecha de corte, promedio final o estado sumativo ingresa jamás al cálculo de $X$. Esto se valida mediante pruebas unitarias automatizadas en `tests/test_ml_pipeline.py`."*

---

### Pregunta 3: "¿Por qué no se utilizó una Red Neuronal Profunda (Deep Learning) o un Modelo de Lenguaje (LLM) para la predicción de riesgo?"
> **Respuesta Clave**:
> *"Por dos principios fundamentales de la ciencia de datos y la pedagogía:*
> 1. ***Principio de Parsimonia en Datos Tabulares**: La literatura científica consolidada (e.g., Grinsztajn et al., 2022; Shwartz-Ziv & Armon, 2022) demuestra empíricamente que los ensambles basados en árboles de decisión (`Random Forest` y `Gradient Boosting`) superan o igualan a las redes neuronales profundas en conjuntos tabulares estructurados de tamaño moderado ($10^3$ a $10^5$ registros), con un costo computacional y una huella de carbono infinitamente menores.*
> 2. ***Inteligencia Artificial Explicable (XAI)**: En el ámbito educativo, un modelo opaco tipo 'caja negra' que solo emite un número arbitrario no resulta útil ni confiable para un docente. Los modelos de ensamble de árboles permiten calcular la importancia relativa de variables y correlacionarla con el perfil del estudiante para generar factores comprensibles en lenguaje natural (ej. 'Bajo rendimiento en evaluaciones formativas', 'Últimas notas muestran tendencia negativa'), facilitando la intervención tutorial focalizada.*
> 
> *(Nota complementaria: El sistema sí utiliza IA Generativa y LLMs locales mediante Ollama, pero delimitada exclusivamente a su propósito idóneo: la generación interactiva de contenidos curriculares y fichas de evaluación formativa)."*

---

### Pregunta 4: "¿Por qué se priorizó el Recall / Sensibilidad sobre la Exactitud (*Accuracy*) para seleccionar al modelo ganador?"
> **Respuesta Clave**:
> *"Por la asimetría crítica en la matriz de costos de error en la analítica educativa:*
> * *Un **Falso Negativo** significa no detectar a un alumno que está por desaprobar. Ese alumno no recibe acompañamiento oportuno y termina reprobando el año escolar. **El costo pedagógico es grave e irreversible**.*
> * *Un **Falso Positivo** significa clasificar preventivamente como 'en riesgo' a un alumno que quizás hubiera aprobado por su cuenta. El resultado de este error es que el estudiante recibe reforzamiento o tutoría adicional positiva, lo cual no le causa ningún perjuicio académico.*
> 
> *Dado que $C(\text{Falso Negativo}) \gg C(\text{Falso Positivo})$, la función de selección de modelos prioriza en primer lugar la **Sensibilidad o Recall de la clase de riesgo** ($90.48\%$), asegurando que más del $90\%$ de los estudiantes en riesgo real sean identificados con anticipación."*

---

### Pregunta 5: "¿Cómo se protege la privacidad de los estudiantes según la legislación vigente?"
> **Respuesta Clave**:
> *"En estricto cumplimiento de la Ley N.º 29733 (Ley de Protección de Datos Personales de la República del Perú):*
> 1. *Ningún dato sensible (nombres, apellidos, número de DNI, correo electrónico, dirección) ingresa a la matriz numérica de entrenamiento $X$.*
> 2. *El código valida mediante aserción matemática (`assert 'student_id' not in feature_cols`) la exclusión permanente de identificadores personales.*
> 3. *Los identificadores se utilizan únicamente a nivel de base de datos relacional para enlazar los registros y para la partición por grupos (`GroupShuffleSplit`), impidiendo cualquier inferencia sobre la identidad del menor."*

---

### Pregunta 6: "¿El modelo sustituye la labor de evaluación del docente?"
> **Respuesta Clave**:
> *"De ninguna manera. El sistema se diseñó bajo el paradigma ético **Human-in-the-Loop (El Humano en el Bucle)**:*
> * *El modelo de Machine Learning es exclusivamente un instrumento de diagnóstico preventivo temprano.*
> * *Toda recomendación, decisión de nivelación o intervención tutorial queda bajo la potestad y criterio pedagógico del docente de aula y del comité de tutoría del colegio.*
> * *La interfaz docente muestra con claridad las advertencias sobre el origen del modelo y los factores que explican la probabilidad estimada."*

---

## 2. Protocolo de Demostración en Vivo para la Sustentación

Para demostrar el funcionamiento del sistema ante el jurado durante la exposición:

### Paso 1: Demostración de Calidad del Código (Terminal)
Ejecutar la suite completa de pruebas automatizadas:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
> **Explicación al jurado**: *"Como se observa en pantalla, las 43 pruebas unitarias y de integración pasan al 100%, cubriendo validación de datos, prevención de fuga temporal, consistencia dimensional y manejo de casos atípicos."*

### Paso 2: Ejecución del Pipeline en un Solo Comando (Terminal)
Ejecutar el orquestador integral:
```powershell
.\.venv\Scripts\python.exe ml/run_pipeline.py --source benchmark --split-strategy temporal
```
> **Explicación al jurado**: *"Con un solo comando, el sistema valida los datos crudos, extrae las 18 variables con aislamiento temporal, compara 4 familias supervisadas y selecciona objetivamente al algoritmo ganador con un Recall superior al 90%."*

### Paso 3: Demostración Visual en la Interfaz Docente (Navegador)
1. Iniciar la aplicación web: `python app.py`.
2. Acceder a `http://localhost:5000` e ingresar con las credenciales de docente (`profesor1`).
3. En el **Dashboard Docente**, seleccionar un alumno de la tabla y visualizar la tarjeta **Predicción académica**.
> **Explicación al jurado**: *"El docente observa en tiempo real la clasificación de riesgo, el porcentaje de probabilidad, el distintivo de modelo y los factores pedagógicos explicables con flechas de alerta, cumpliendo con los estándares de explicabilidad y transparencia algorítmica."*
