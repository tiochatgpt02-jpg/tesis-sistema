# Verificación de generación desde material docente

Este archivo sustituye el informe heredado de Ollama. El despliegue actual utiliza Groq; no se necesita un servidor local de modelos.

## Evidencia disponible

En la revisión del 15 de noviembre se generó un juego de completar desde el PPT de SmartArt para quinto. La respuesta SMARTART se contrastó con el contenido del archivo docente. En la web publicada la generación demoró 1.110 segundos y el envío de una respuesta al juego 0.150 segundos. Se comprobó que jugar no añadió notas académicas y se limpiaron los datos temporales de esa prueba.

Se verificaron formularios visuales para los ocho tipos de juegos. La estructura válida de un juego no demuestra por sí sola que su contenido sea pedagógicamente correcto: el docente debe comprobar preguntas, claves, distractores y adecuación al grado antes de publicar.

## Tratamiento de fallos

Si la API no responde o el contenido no supera la validación, el sistema identifica el respaldo determinista. Ese resultado requiere revisión y no cuenta como éxito real de IA. El alumno utiliza contenido previamente guardado y no consulta al proveedor durante la respuesta.

Las mediciones corresponden a una muestra y no garantizan tiempos futuros. Los límites de cuota, conexión y despertar de Render pueden cambiar el tiempo observado. Ver [evidencia técnica](validacion-cambios-nube.md) y [protocolo del piloto](protocolo-piloto.md).
