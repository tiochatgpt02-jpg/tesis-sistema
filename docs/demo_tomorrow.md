# Demo de mañana

## 1. Arrancar los servicios

Abre PowerShell como administrador y verifica PostgreSQL:

```powershell
Get-Service postgresql-x64-18
Start-Service postgresql-x64-18
```

En otra consola, comprueba Ollama:

```powershell
ollama list
```

Debe aparecer `llama3.2:1b`. Si Ollama no está iniciado, ejecuta:

```powershell
ollama serve
```

Desde la carpeta `sistema IA\sistema IA`, inicia la aplicación:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 2. Cuentas de demo

- Profesor: `profesor1`
- Alumno de 4.º: `alumno4_demo`
- Alumno de 5.º: `alumno5_demo`
- Alumno de 6.º: `alumno6_demo`

Las contraseñas se mantienen en la hoja privada de credenciales; no se muestran aquí.

## 3. Orden recomendado

### Demo 1: profesor

1. Inicia sesión como profesor y abre **Actividades**.
2. En el generador de juegos selecciona 5.º, **El ciclo del agua**, fuente **Presentación PPTX de la Sesión** y tipo **Ordenar Conceptos**.
3. Muestra el juego publicado: `Evaporación → Condensación → Precipitación y colección`.
4. Explica el flujo de control: generado, revisado, aprobado y publicado. No publiques contenido sin revisarlo.
5. En **Evaluaciones IA**, abre la evaluación formal de **El ciclo del agua**: muestra 15 preguntas. Revisa, aprueba y publica sólo si creas una nueva evaluación.

### Demo 2: alumno

1. Cierra sesión e ingresa como alumno de 6.º.
2. En **Mis clases**, abre **Sesión 1** y el material **Microsoft Excel**.
3. Abre **Juego educativo**, resuelve el Quiz publicado y muestra el mensaje de resultado.
4. El sistema guarda directamente el intento, respuesta, puntaje y tiempo en PostgreSQL.
5. Como segunda vista, ingresa como alumno de 5.º, abre **El ciclo del agua** y muestra la evaluación formal de 15 preguntas.

### Demo 3: separación por grado

1. Ingresa como alumno de 4.º y abre **El presupuesto**.
2. En **Practicar**, muestra las cuatro preguntas con sus fragmentos de referencia del PPT.
3. Comprueba la separación por grado: 4.º **El presupuesto**, 5.º **Encuestas para el estudio de mercado** y **SmartArt**, 6.º **Microsoft Excel**.

## 4. Si Ollama tarda o falla

- Espera hasta 30 segundos en la generación antes de repetir una sola vez.
- En la consola de Flask revisa: `[AI] modelo`, `[AI] material` y `[AI] source`.
- `source: ollama` significa que la respuesta válida provino del modelo.
- `source: fallback` significa que el modelo no devolvió JSON válido y el sistema creó contenido determinista basado únicamente en el texto extraído del PPT. No lo presentes como respuesta de Ollama.
- Para evitar demoras durante la exposición, usa los juegos y la evaluación ya publicados si la generación en vivo se demora.
