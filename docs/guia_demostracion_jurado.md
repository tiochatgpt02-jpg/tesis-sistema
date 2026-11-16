# Guía para demostrar el sistema publicado

Abrir https://aula-computacion-tesis.onrender.com con anticipación. Render Free puede tardar en despertar. No se necesita iniciar Ollama ni PostgreSQL en las laptops. Usar las cuentas de docente y alumno administradas en la hoja privada; las credenciales locales antiguas no son las del despliegue.

## Recorrido docente y alumno

1. En la laptop docente, abrir el tema del grado y mostrar su presentación. Para la demostración preparada se ha utilizado SmartArt en quinto. Los materiales de otros grados deben ser confirmados por el docente.
2. Generar un juego desde esa presentación, revisar que pregunta, alternativas y respuesta correspondan al PPT y editar con los formularios. Si aparece respaldo, identificarlo como tal; no afirmar que proviene de IA.
3. Aprobar y publicar. En la laptop del alumno, abrir la clase y resolver el juego. Mostrar que los puntos de entrenamiento no se incorporan como notas.
4. Crear prácticas y examen desde el material. Seleccionar tipo y cantidad de preguntas, revisar claves y publicar. El alumno abre la vista previa y luego pulsa Comenzar. Una práctica admite repetición; el examen tiene treinta minutos desde Comenzar y requiere reapertura docente para otro intento.
5. En la libreta, elegir grado, año y bimestre. Vincular práctica 1, práctica 2 y examen; registrar manualmente tareas, participación y libro. Las notas automáticas provienen del último intento del periodo. Una nota pendiente no es cero.
6. Mostrar el historial institucional: cuarto tiene quince registros del primer bimestre de 2026 en AD/A/B/C, conservados sin conversión numérica. No confundirlos con la libreta nueva ni con las mediciones pretest y postest de la tesis.
7. Mostrar calendario y cierre. Las fechas referenciales de 2026 están sin confirmar; no marcar aprobación escolar para obtener una demostración de cierre. Usar un entorno ficticio para esa prueba mientras falta la confirmación.
8. Mostrar la ficha ML y su aviso de referencia pública. No prometer una probabilidad determinada ni precisión con los alumnos del colegio.

Usar cuentas ficticias para crear notas de prueba. No llenar registros reales para eliminar pendientes. Al terminar, cerrar sesión en ambos equipos y conservar la evidencia autorizada del piloto.

## Respuestas breves al jurado

- Arquitectura técnica: monolito modular Flask con Blueprints, servicios, plantillas y PostgreSQL remoto. [Expediente TOGAF 9.2](arquitectura-togaf-9-2.md) relaciona negocio, datos, aplicaciones, tecnología y gobierno; no acredita certificación ni uso retrospectivo desde el inicio.
- IA generativa: crea borradores basados en PPT; el docente decide qué se publica. Resolver una actividad no llama a la API.
- Machine Learning: usa un benchmark público de secundaria. Su evaluación revisada separa elección y prueba; no está validado institucionalmente.
- Datos reales: las cuentas y el historial literal están en PostgreSQL. Tener 51 cuentas no demuestra que 51 personas participaron en un nuevo piloto.
- Privacidad: se aplican roles, acceso al propio historial y hashes de contraseñas. Estas medidas no equivalen por sí solas a una certificación de cumplimiento legal.

La mejora de aprendizaje reportada por una investigación y la precisión predictiva del software son evidencias diferentes. Las cifras de la tesis deben contrastarse con sus instrumentos originales.
