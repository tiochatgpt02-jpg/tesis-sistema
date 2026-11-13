# Guía de Pruebas para Docentes y Usuarios No Técnicos

Bienvenido al manual interactivo de pruebas de **Sistema IA**. Esta guía está diseñada para que docentes, directores, evaluadores y jurados puedan verificar de manera sencilla, intuitiva y visual el funcionamiento del sistema de predicción temprana de riesgo académico escolar.

---

## 1. ¿Cómo Iniciar el Sistema?

### Paso 1: Abrir la Terminal
En tu computadora con Windows, abre PowerShell o la terminal dentro de la carpeta del proyecto:
```powershell
.\.venv\Scripts\python.exe app.py
```

Deberás ver un mensaje confirmando que el servidor web está activo:
```text
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Paso 2: Abrir el Navegador Web
Abre tu navegador preferido (Google Chrome, Edge, Firefox) e ingresa a la siguiente dirección:
👉 **`http://localhost:5000`** o **`http://127.0.0.1:5000`**

---

## 2. Inicio de Sesión como Docente

1. En la pantalla de bienvenida, haz clic en **"Iniciar Sesión"**.
2. Ingresa con las credenciales de profesor de prueba:
   * **Usuario**: `profesor1`
   * **Contraseña**: `profesor1` (o la contraseña configurada en la base de datos)
3. Haz clic en **Ingresar**. El sistema te llevará directamente al **Panel Principal del Docente (Dashboard)**.

---

## 3. Exploración de la Tarjeta "Predicción Académica"

En el panel docente, en la columna derecha de la sección de calificaciones, encontrarás la tarjeta especializada de **Predicción académica**:

```
+-----------------------------------------------------------------+
|  📈 Predicción académica                                        |
+-----------------------------------------------------------------+
|  👤 Alumno: Carlos Mendoza               [ Chip: En proceso ]   |
|                                                                 |
|  +---------------------------+   +---------------------------+  |
|  |  Riesgo                   |   |  Probabilidad             |  |
|  |  ALTO                     |   |  98.8%                    |  |
|  +---------------------------+   +---------------------------+  |
|                                                                 |
|  📋 Factores principales:                                       |
|  ↓ Bajo rendimiento en evaluaciones formativas (promedio < 11)  |
|  ↓ Últimas notas muestran tendencia fuertemente negativa        |
|  ↓ Última calificación registrada en nivel reprobatorio         |
|                                                                 |
|  Recomendación: Priorizar refuerzo en áreas críticas y tutoría. |
|                                                                 |
|  ⚙️ Modelo: Random Forest              [ Badge: Benchmark ]     |
|  ℹ️ Este modelo actualmente usa dataset público. Para uso        |
|     institucional requiere entrenamiento con datos del colegio. |
|                                                                 |
|  [ 🔄 Actualizar predicción académica ]                         |
+-----------------------------------------------------------------+
```

### ¿Qué significa cada elemento para el docente?

1. **Riesgo (ALTO, MEDIO, BAJO)**:
   * 🔴 **ALTO**: El estudiante presenta una alta probabilidad de reprobar la materia al cierre del periodo lectivo si no se interviene a tiempo.
   * 🟡 **MEDIO**: Rendimiento inestable o borderline. Requiere seguimiento formativo y tareas complementarias.
   * 🟢 **BAJO**: El estudiante mantiene calificaciones aprobatorias y un progreso formativo seguro.
2. **Probabilidad (%)**: La certeza matemática calculada por el algoritmo supervisado.
3. **Factores Principales (`↓`)**: El "por qué" de la predicción en lenguaje natural docente (XAI):
   * Informa si el alumno bajó sus notas recientemente.
   * Informa si reprobó exámenes clave.
   * Informa si completó pocas actividades en el aula virtual.
4. **Distintivo y Aviso de Modelo**:
   * Indica con transparencia si el modelo activo proviene del **Benchmark Académico** (dataset público) o del **Modelo Institucional** (datos reales del colegio).

---

## 4. Casos de Prueba Recomendados para Demostración

Para verificar cómo responde el sistema ante diferentes realidades de aula, prueba estos tres perfiles:

### Caso A: Estudiante con Calificaciones en Riesgo
1. En la tabla de notas, selecciona a un estudiante con notas bajas (por ejemplo, con notas formativas de 06 y 07).
2. Observa la tarjeta de predicción:
   * **Riesgo**: Cambiará inmediatamente a 🔴 **ALTO**.
   * **Probabilidad**: Mostrará un valor elevado (entre $85\%$ y $99\%$).
   * **Factores**: Indicará claramente que el promedio está por debajo de 11 y que las notas muestran tendencia descendente.
   * **Recomendación**: Sugiere tutoría personalizada y acompañamiento pedagógico focalizado.

### Caso B: Estudiante con Desempeño Destacado
1. Selecciona a un alumno con notas aprobatorias sólidas (por ejemplo, 16 o 17).
2. Observa la tarjeta de predicción:
   * **Riesgo**: Cambiará a 🟢 **BAJO**.
   * **Probabilidad**: Se situará en valores mínimos (menores al $15\%$).
   * **Factores**: Destacará el progreso constante y la participación activa en el periodo.
   * **Recomendación**: Sugiere proponer desafíos de mayor complejidad y mantener el ritmo de aprendizaje.

### Caso C: Estudiante Nuevo o Sin Historial de Notas
1. Selecciona a un alumno que no tenga actividades ni notas cargadas.
2. Observa la tarjeta de predicción:
   * **Riesgo**: Se marcará como **Sin datos** / **Indeterminado**.
   * **Probabilidad**: No mostrará porcentajes artificiales (`--%`).
   * **Factores**: Indicará honestamente: *"Sin historial previo de notas o actividades registradas para este estudiante"*.

---

## 5. ¿Cómo Reentrenar el Modelo con un Solo Comando?

Si deseas demostrar a los evaluadores o al jurado cómo se procesa y reentrena el modelo de Machine Learning desde cero:

1. Abre la terminal en la raíz del proyecto.
2. Ejecuta el orquestador automático:
```powershell
.\.venv\Scripts\python.exe ml/run_pipeline.py
```
3. En menos de 1 segundo verás cómo la terminal:
   * Valida la calidad del archivo de datos.
   * Extrae las 18 características respetando la fecha de corte.
   * Compara los 4 algoritmos (`Random Forest`, `Gradient Boosting`, `Logistic Regression`, `Decision Tree`).
   * Elige al mejor algoritmo priorizando la detección de riesgo (Recall $> 90\%$).
   * Guarda el modelo actualizado listo para ser consumido por el navegador.

---

## 6. Preguntas Frecuentes (FAQ) para Docentes

**¿La IA desaprueba a los estudiantes automáticamente?**  
No. La predicción es una **herramienta orientativa y de apoyo diagnóstico**. La calificación oficial y las decisiones académicas son y serán siempre responsabilidad exclusiva del profesor de aula.

**¿El sistema comparte los nombres o DNI de mis alumnos en internet?**  
No. El modelo se ejecuta de manera **100% local en el servidor del colegio**. Ningún dato personal (nombres, DNI, correos) se utiliza para entrenar la inteligencia artificial, protegiendo la privacidad de los estudiantes según la Ley N.º 29733 del Perú.

**¿Qué pasa si mi colegio tiene calificaciones propias?**  
El administrador del colegio puede ingresar los registros históricos en formato CSV y ejecutar el importador institucional para que el sistema aprenda directamente de los datos reales de su propia escuela.
