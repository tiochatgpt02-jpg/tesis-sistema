# Verificación de calidad de Ollama

Fecha de prueba: 25 de septiembre de 2026.

Modelo configurado: `llama3.2:1b`.

## Materiales revisados

| Archivo | Título extraído | Uso en la demo |
| --- | --- | --- |
| `ciclo_del_agua_prueba_v1.pptx` | El ciclo del agua | Sí, 5.º de primaria |
| `TEORIA 1.pptx` | Encuestas para el estudio de mercado | Sí, 5.º, sesión 1 |
| `TEORIA 2.pptx` | SmartArt | Sí, 5.º, sesión 2 |
| `TEORIA 3.pptx` | El presupuesto | Sí, 4.º, sesión 1 |
| `TEORIA 4.pptx` | Microsoft Excel | Sí, 6.º, sesión 1 |

Aunque algunas diapositivas conservan rótulos de otro nivel, el docente confirmó que los cuatro archivos son el material de primaria que debe utilizarse. La asignación anterior es la autoridad para esta demo.

## Batería sobre El ciclo del agua

| Tipo | Resultado | Fuente | Observación |
| --- | --- | --- | --- |
| Quiz | Aprobado | Ollama | Tres ejecuciones devolvieron una respuesta literal del PPT: el agua cambia de lugar y de estado. Las alternativas son cortas y la respuesta es válida. |
| True / False | Aprobado | Ollama | La afirmación cita la primera idea del PPT. |
| Matching | Aprobado para demo | Fallback | Ollama devolvió etiquetas genéricas. El respaldo crea Evaporación, Condensación y Precipitación con evidencia de cada sección. |
| Ordering | Aprobado para demo | Fallback | Ollama devolvió pasos vacíos. El respaldo usa el orden real Evaporación, Condensación y Precipitación. |
| Fill Blank | Funcional, no recomendado | Fallback | Forma una oración literal: `El ____ cambia de lugar y de estado...`. |
| Memory | No recomendado | Fallback | La estructura puede reutilizar parejas correctas, pero la salida del modelo no fue consistente ni rápida. |
| Drag & Drop | No recomendado | Sin publicación | Requiere validación visual adicional antes de mostrarlo. |
| Adventure | No recomendado | Sin publicación | Requiere validación visual adicional antes de mostrarlo. |

## Fallos detectados y controles aplicados

1. El modelo pequeño podía copiar textos genéricos del ejemplo, como `Primer paso` u `Opción correcta`.
2. Ahora las validaciones rechazan esos marcadores aunque el JSON sea formalmente válido.
3. Cada generación intenta reparar o regenerar una vez. Si continúa inválida, usa un respaldo determinista basado sólo en texto extraído del PPT.
4. Los registros de desarrollo indican siempre modelo, material, tipo y `source: ollama` o `source: fallback`.
5. En la prueba de `El presupuesto`, `llama3.2:1b` devolvió alternativas repetidas y después distractores de otro tema. La validación ahora rechaza alternativas duplicadas o sin evidencia del PPT; el respaldo usa `Monto Total`, `División de gastos`, `Lista de gastos` y `Monto calculado de cada gasto`.

## Repetición y comparación de modelos

La auditoría reproducible está en `scripts/ollama_repetition_audit.py`. Sus salidas locales se conservan en `.logs/` y no escriben actividades ni alteran PostgreSQL.

| Modelo | Muestra | Resultado validado | Tiempo observado | Decisión |
| --- | --- | --- | --- | --- |
| `llama3.2:1b` (1.3 GB) | 3 ejecuciones por cada uno de los 4 PPT (12) | 12 fallback: sus alternativas no tenían evidencia suficiente en el PPT | 8.7–21.2 s | Mantenerlo como modelo principal con filtro y fallback. |
| `llama3.2:3b` (2.0 GB) | 1 ejecución por cada PPT (4) | Sólo presupuesto pasó como salida del modelo; 3 fallback | 15.8–27.6 s | No reemplazar: calidad irregular y más lento. |
| `llama3:latest` (4.7 GB) | 1 muestra de presupuesto | Fallback por alternativas sin evidencia | 53.6 s | No es razonable para una demostración local. |

La comparación usó procesos aislados con la variable `OLLAMA_MODEL`; el archivo `.env` y el servidor siguen configurados con `llama3.2:1b`.

## Conclusión para la presentación

El modelo principal sigue siendo `llama3.2:1b`; no se modificó. Su salida no fue suficientemente consistente para publicar sin controles: en los cuatro PPT produjo alternativas no respaldadas por la fuente en la batería repetida. El sistema las rechazó y usó sólo el respaldo determinista trazable al PPT.

Para la sustentación hay tres tipos publicados y revisados: opción múltiple, unir conceptos y ordenar conceptos. El juego de ordenar publicado usa `Evaporación → Condensación → Precipitación y colección`; la revisión docente muestra las tres tarjetas antes de publicarlo. No se recomienda demostrar memoria, arrastrar/clasificar ni aventura: no alcanzaron una calidad estable con este modelo pequeño.

La prueba de navegador verificó además una práctica de 4.º sobre `El presupuesto`: sus cuatro preguntas muestran el fragmento fuente correspondiente. Se completó un Quiz de 6.º sobre `Microsoft Excel` y PostgreSQL registró el intento, respuesta, puntaje y tiempo. La vista móvil a 390 px quedó sin desborde horizontal después de ajustar el encabezado docente.
