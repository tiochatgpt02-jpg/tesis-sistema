# Guía Rápida de Demostración del Sistema IA

Esta guía de **5 pasos** permite a cualquier persona (tesista, docente o jurado) poner en marcha el sistema y comprobar el funcionamiento de la Inteligencia Artificial predictiva en menos de **3 minutos**.

---

## Paso 1. Iniciar el Sistema (1 Clic)

1. En la carpeta principal del proyecto, haga **doble clic** en el archivo:
   ```text
   iniciar_sistema.bat
   ```
2. El sistema verificará el entorno y **abrirá automáticamente el navegador web** en:  
   `http://127.0.0.1:5000/login`

> [!NOTE]
> No es necesario abrir terminales ni escribir comandos. Si no tiene MySQL instalado o activo, el sistema activará automáticamente el modo demostración para que todo funcione sin interrupciones.

---

## Paso 2. Entrar como Profesor

En la pantalla de inicio de sesión:
* **Opción A (Recomendada - 1 Clic):** Presione el botón azul:  
  **`[ Ingresar como Profesor (Demo) ]`**
* **Opción B (Manual):**  
  * **Usuario:** `profesor1`  
  * **Contraseña:** `Admin123`

Presione **Ingresar a Computación**. Accederá inmediatamente al panel principal del profesor (*Prof. Roberto Sánchez*).

---

## Paso 3. Seleccionar Alumno

1. En el menú lateral izquierdo (o en la tarjeta de bienvenida), haga clic en **`Reportes`** (o en el botón azul de inicio **`[ Predicción de riesgo IA ]`**).
2. Se desplegará la tabla de rendimiento con las notas vigesimales ($0$ a $20$) del aula.
3. El primer alumno se selecciona automáticamente. Para evaluar a otro alumno, simplemente **haga clic sobre su fila en la tabla**:
   * **Juan Pérez (5.º Grado):** Alumno con notas bajas y tendencia descendente.
   * **María García (5.º Grado):** Alumna con rendimiento intermedio / moderado.
   * **Carlos López o Ana Martínez:** Alumnos con calificaciones aprobatorias consolidadas.

---

## Paso 4. Ver la Predicción de Riesgo

Mire la tarjeta **`Predicción académica`** ubicada debajo de la tabla. Al seleccionar al estudiante, el modelo de Machine Learning supervisado calcula al instante:
* **Nivel de Riesgo:**
  * <span style="color:#dc2626; font-weight:bold;">Alto</span> (para estudiantes con alto riesgo de reprobar o necesitar apoyo crítico).
  * <span style="color:#f59e0b; font-weight:bold;">Medio</span> (estudiante en rango intermedio de atención preventiva).
  * <span style="color:#16a34a; font-weight:bold;">Bajo</span> (estudiante en trayectoria aprobatoria estable).
* **Probabilidad Calibrada:** Porcentaje estimado de vulnerabilidad (por ejemplo: `99.8%`, `64.2%` o `0.0%`).
* **Recomendación Pedagógica:** Acción tutorial sugerida al docente.

---

## Paso 5. Interpretar los Factores Determinantes (IA Explicable - XAI)

Debajo de las métricas de la tarjeta, revise la sección **`Factores principales`**:
* Cada factor viene acompañado de una flecha indicativa (`↓`) redactada en lenguaje pedagógico claro:
  * *↓ Bajo rendimiento en evaluaciones formativas (promedio menor a 11)*
  * *↓ Últimas notas muestran tendencia fuertemente negativa*
  * *↓ Última calificación registrada en nivel reprobatorio (5.0/20)*
* **Significado para el Jurado:** El sistema no es una "caja negra"; no se limita a predecir, sino que transparenta las razones del riesgo para orientar la intervención docente.
* **Ficha Técnica:** Puede presionar el botón **`[ Ver Ficha Técnica del Modelo ]`** para mostrar al jurado las métricas de validación:
  * **Algoritmo:** Random Forest Classifier (Ensemble)
  * **Sensibilidad (Recall):** 90.48%
  * **Exactitud (Accuracy):** 91.15%
  * **ROC-AUC:** 0.9605
  * **Privacidad:** Ley N.º 29733 (cero nombres ni identificadores en la matriz de features).

---

## Para Cerrar el Sistema

1. Haga clic en el botón de salida en la esquina superior derecha (`Cerrar sesión`).
2. Cierre la ventana negra de la consola o presione `Ctrl + C`.
