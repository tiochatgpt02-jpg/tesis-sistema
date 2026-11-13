# Metodología y Fundamentación Científica del Modelo Predictivo

## 1. Planteamiento del Problema y Justificación Teórica

La deserción y el fracaso escolar representan problemáticas estructurales en la educación secundaria. En los modelos tradicionales de gestión escolar, la evaluación sumativa se consolida al cierre de los bimestres o del año académico, momento en el cual las posibilidades de intervención tutorial o nivelación pedagógica resultan tardías e ineficaces.

Este proyecto formula un enfoque de **Supervised Machine Learning** basado en series temporales de evaluación formativa para estimar, de manera precoz y automatizada, la probabilidad a posteriori de que un estudiante concluya el periodo académico en condición de riesgo o desaprobación. 

Para garantizar la validez científica del modelo, el sistema implementa un mecanismo estricto de **aislamiento temporal (anti-leakage)** mediante una fecha de corte (`cutoff_date`), asegurando que las variables predictivas ($X$) se calculen exclusivamente a partir de eventos ocurridos antes de dicha fecha, sin contaminación retrospectiva del resultado final ($y$).

---

## 2. Definición del Dataset y Mapeo Epistemológico

### 2.1. Dataset de Benchmark Internacional
Para la validación técnica, algorítmica y arquitectónica del pipeline se utilizó el dataset canónico **Student Performance Data Set** (*Cortez & Silva, 2008*), alojado en el repositorio UCI Machine Learning Repository.

* **Referencia Formal**: Cortez, P., & Silva, A. (2008). *Using data mining to predict secondary school student performance*. In Proceedings of 5th Annual Future Business Technology Conference (FUBUTEC 2008), pp. 5-12, Porto, Portugal. EUROSIS-ETI, ISBN 978-9077381-39-7.
* **Contexto de Recolección**: Estudiantes de dos instituciones de educación secundaria en la región de Alentejo, Portugal (Escola Secundária Gabriel Pereira y Escola Secundária Mousinho da Silveira) durante el año académico 2005–2006.
* **Muestreo**: 1,044 registros correspondientes a dos materias troncales: Matemática ($n=395$) y Lengua Portuguesa ($n=649$).
* **Mapeo a la Escala Vigesimal Oficial (0 a 20)**:
  * El sistema educativo portugués de educación secundaria califica formalmente en una escala vigesimal entera de $0$ a $20$, donde la nota mínima de suficiencia es $10$.
  * En el sistema educativo peruano (RVM N.º 094-2020-MINEDU / CNEB), la escala vigesimal oficial también opera en el rango de $0$ a $20$, con la diferencia técnica de que la nota mínima aprobatoria es **$11.0$** (calificación 'B' o superior), considerándose el intervalo $[0, 10]$ como condición de riesgo o desaprobación ('C').
  * **Alineación**: Para preservar la congruencia con la normativa educativa peruana, se adoptó el umbral $y=1$ para calificaciones finales menores estrictas a $11.0$ ($\text{score} < 11.0$), clasificando el intervalo vigesimal $[0, 10]$ como riesgo académico real.

### 2.2. Diseño Experimental de la Partición Temporal
En el benchmark de Cortez & Silva, los estudiantes cuentan con tres evaluaciones secuenciales:
1. $G_1$: Calificación del primer periodo formativo intermedio.
2. $G_2$: Calificación del segundo periodo formativo intermedio.
3. $G_3$: Calificación final consolidada del periodo escolar.

Para validar de forma rigurosa la capacidad de generalización temporal del pipeline escolar:
* Se mapearon los eventos $G_1$ y $G_2$ como registros cronológicos de actividades y evaluaciones previas a la fecha de corte (`2024-04-30`).
* Se distribuyeron las observaciones en dos cohortes lectivas:
  * **Cohorte 2023 (Train)**: 626 estudiantes (60% del dataset), utilizados como histórico previo para el ajuste de hiperparámetros.
  * **Cohorte 2024 (Test out-of-time)**: 418 estudiantes (40% del dataset), preservados intactos como conjunto ciego de evaluación temporal futura.

---

## 3. Definición de la Variable Objetivo ($y$) y Espacio de Entrada ($X$)

### 3.1. Variable Objetivo (Target Binario)
La variable objetivo $y_i \in \{0, 1\}$ denota el desenlace académico del estudiante $i$:

$$y_i = \begin{cases} 1 & \text{si } \text{final\_score}_i < 11.0 \lor \text{final\_status}_i \in \{\text{'desaprobado'}, \text{'reprobado'}, \text{'en\_riesgo'}\} \\ 0 & \text{si } \text{final\_score}_i \ge 11.0 \land \text{final\_status}_i = \text{'aprobado'} \end{cases}$$

Distribución de clases en el benchmark:
* **Clase Negativa ($y=0$, Aprobado)**: $661$ estudiantes ($63.3\%$).
* **Clase Positiva ($y=1$, Riesgo Académico)**: $383$ estudiantes ($36.7\%$).

### 3.2. Espacio de Características Predictivas ($X \in \mathbb{R}^{18}$)
Todas las características son calculadas determinísticamente por `ml.pipeline.feature_builder` respetando la condición anti-leakage:

$$\mathcal{E}_i^{(\le t_c)} = \{e \in \mathcal{E}_i \mid \text{fecha}(e) \le t_{\text{cutoff}}\}$$

1. `total_attempts`: Cardinalidad $|\mathcal{E}_i^{(\le t_c)}|$ de eventos registrados.
2. `evaluation_count`: Cantidad de exámenes formales en el periodo.
3. `activities_count`: Cantidad de tareas y fichas de aula completadas.
4. `games_count`: Participación en dinámicas formativas interactivas.
5. `average_score`: Media aritmética global $\bar{s} = \frac{1}{N}\sum_{j=1}^N s_j$.
6. `average_evaluation_score`: Media aritmética restringida a evaluaciones formales.
7. `average_activity_score`: Media aritmética restringida a actividades de clase.
8. `min_score`: Calificación mínima $\min(s_j)$ registrada antes del corte.
9. `max_score`: Calificación máxima $\max(s_j)$ registrada antes del corte.
10. `last_score`: Calificación del evento formativo más reciente $s_N$.
11. `score_std`: Desviación estándar muestral $\sigma_s = \sqrt{\frac{1}{N}\sum (s_j - \bar{s})^2}$.
12. `score_trend`: Gradiente de evolución temporal ($\bar{s}_{\text{segunda mitad}} - \bar{s}_{\text{primera mitad}}$).
13. `total_correct_answers`: Total de aciertos en reactivos interactivos.
14. `total_wrong_answers`: Total de errores en reactivos interactivos.
15. `accuracy_ratio`: Tasa de acierto $\frac{\text{correctas}}{\text{correctas} + \text{incorrectas}}$.
16. `average_time_spent_seconds`: Tiempo medio de resolución en segundos.
17. `materials_reviewed_count`: Documentos curriculares consultados.
18. `submissions_count`: Entregas de tareas registradas.

---

## 4. Algoritmos Comparados y Formulación Matemática

El pipeline compara cuatro familias arquetípicas del aprendizaje supervisado:

### 4.1. Regresión Logística Regularizada ($L_2$)
Modela la probabilidad condicional $P(y=1 \mid \mathbf{x}) = \sigma(\mathbf{w}^T \mathbf{x} + b)$, minimizando la función de costo Log-Loss penalizada:

$$\mathcal{L}_{\text{LR}}(\mathbf{w}, b) = -\frac{1}{M}\sum_{i=1}^M \left[ y_i \ln(\hat{p}_i) + (1 - y_i) \ln(1 - \hat{p}_i) \right] + \frac{\lambda}{2} \|\mathbf{w}\|_2^2$$

### 4.2. Árbol de Decisión (CART)
Particiona recursivamente el espacio de características maximizando la reducción de impureza de Gini en cada nodo $t$:

$$I_G(t) = 1 - \sum_{k=0}^1 p(k \mid t)^2$$

Se acota la profundidad máxima (`max_depth=5`, `min_samples_split=10`) para prevenir el sobreajuste (*overfitting*).

### 4.3. Bosque Aleatorio (Random Forest)
Ensamble de embolsado (*Bagging*) de $B=100$ árboles de decisión no correlacionados, entrenados sobre muestras bootstrap con subespacios aleatorios de características ($m = \sqrt{D}$):

$$\hat{P}_{\text{RF}}(y=1 \mid \mathbf{x}) = \frac{1}{B}\sum_{b=1}^B T_b(\mathbf{x})$$

### 4.4. Potenciación del Gradiente (Gradient Boosting)
Ajuste aditivo secuencial de $K=100$ estimadores base débiles (árboles de profundidad reducida) que optimizan pseudo-residuos negativos del gradiente:

$$F_m(\mathbf{x}) = F_{m-1}(\mathbf{x}) + \gamma_m h_m(\mathbf{x})$$

---

## 5. Justificación de la Matriz de Costos y Criterio de Selección

En analítica predictiva escolar existe una asimetría crítica en los costos de error:

| Diagnóstico del Modelo | Realidad: Alumno Reprueba ($y=1$) | Realidad: Alumno Aprueba ($y=0$) |
| :--- | :--- | :--- |
| **Predice Riesgo ($\hat{y}=1$)** | **Verdadero Positivo (VP)**: Intervención tutorial oportuna. | **Falso Positivo (FP)**: Acompañamiento preventivo a un alumno que no lo requería críticamente. Costo: Bajo. |
| **Predice Sin Riesgo ($\hat{y}=0$)** | **Falso Negativo (FN)**: Alumno en riesgo desatendido que termina reprobando sin ayuda. **Costo: Crítico**. | **Verdadero Negativo (VN)**: Desempeño normal sin intervención. |

Dado que el costo pedagógico de un Falso Negativo supera ampliamente al de un Falso Positivo ($C(FN) \gg C(FP)$), la selección del modelo ganador prioriza:
1. **Recall / Sensibilidad de Riesgo**: $\frac{VP}{VP + FN}$
2. **F1-Score de Riesgo**: Media armónica entre Precisión y Recall.
3. **ROC-AUC**: Discriminación global ante variaciones de umbral.

### Resultados Empíricos en Holdout Temporal (2024-B1, 418 muestras out-of-time)

| Modelo | Accuracy | Precisión ($y=1$) | Recall ($y=1$) | F1-Score ($y=1$) | ROC-AUC | Selección |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** | **91.15%** | **90.00%** | **90.48%** | **0.9024** | **0.9605** | **GANADOR** |
| **Gradient Boosting** | 91.15% | 90.00% | 90.48% | 0.9024 | 0.9572 | Candidato 2 |
| **Logistic Regression** | 91.15% | 91.30% | 88.89% | 0.9008 | 0.9676 | Candidato 3 |
| **Decision Tree** | 91.15% | 91.30% | 88.89% | 0.9008 | 0.9543 | Candidato 4 |

---

## 6. Declaración Explícita de Limitaciones y Marco Ético

> [!IMPORTANT]
> **Postura Metodológica para la Tesis**:
> El modelo benchmark demuestra rigurosamente la viabilidad técnica, algorítmica y reproducible del pipeline escolar. Sin embargo, **la validez institucional y el despliegue operativo en una escuela concreta requieren obligatoriamente el reentrenamiento del pipeline (`python ml/run_pipeline.py --source institutional`) utilizando las calificaciones y registros históricos propios de dicha institución**.

* **Supervisión Humana en el Bucle (*Human-in-the-Loop*)**: El modelo tiene propósito exclusivamente orientador y preventivo. Bajo ninguna circunstancia reemplaza el criterio pedagógico del docente o comité tutorial.
* **Protección de Datos Personales (Ley N.º 29733 en el Perú)**: Ningún identificador personal (nombres, DNI, correo) ingresa a la matriz numérica $X$.
