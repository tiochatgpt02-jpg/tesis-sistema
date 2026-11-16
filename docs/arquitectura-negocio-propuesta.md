# Arquitectura de negocio propuesta para el aula de computación

Documento histórico. La revisión vigente con reglas, brechas, gobierno y evidencia se encuentra en [Arquitectura con TOGAF 9.2](arquitectura-togaf-9-2.md) y [Libreta bimestral](libreta-bimestral.md). La aceptación institucional se registra por separado.


Este documento describe una propuesta de alcance de arquitectura de negocio alineada con las observaciones comunicadas del jurado. No afirma una implementación completa ni certificación de TOGAF. La descripción del proceso previo debe validarse con el docente y las tesistas; el repositorio por sí solo no demuestra cómo trabajaba el colegio antes de la intervención.

## Propósito y participantes

El propósito del sistema es apoyar el aprendizaje de computación de cuarto, quinto y sexto de primaria y permitir evaluar y seguir los resultados académicos. El estudiante consulta materiales, entrena, practica y rinde exámenes. El docente prepara contenido, revisa la generación de IA, publica actividades, califica entregas, autoriza reaperturas e interviene ante dificultades. La dirección o responsable académico valida las reglas de evaluación. El responsable técnico administra acceso, datos y disponibilidad.

## Capacidades y proceso objetivo

| Capacidad | Resultado de negocio | Responsable principal |
| --- | --- | --- |
| Preparar enseñanza | Material correspondiente a un grado, sección y sesión | Docente |
| Ofrecer entrenamiento | Juegos opcionales que permiten practicar sin alterar notas | Docente y estudiante |
| Evaluar prácticas | Evidencia de desempeño con preguntas y calificación reproducible | Docente |
| Aplicar exámenes | Evaluación de mayor peso con intento y plazo controlados | Docente |
| Consolidar calificaciones | Notas del periodo con pesos explícitos y trazabilidad | Docente y responsable académico |
| Acompañar aprendizaje | Refuerzo relacionado con dificultades observadas | Docente |

El recorrido objetivo es preparar material, publicar, permitir entrenamiento, realizar práctica calificada, rendir examen, revisar resultados y asignar refuerzo. Los juegos pueden usarse libremente; no son un requisito para obtener una nota ni un sustituto del examen.

## Reglas de negocio acordadas y decisiones pendientes

- Los juegos no dan calificación académica ni cambian promedios.
- Una práctica o examen se ofrece a los alumnos del grado y sección correspondiente.
- Las prácticas admiten nuevos intentos.
- El examen admite un intento; otro requiere reapertura docente.
- La nota se calcula con las preguntas y claves que correspondían al intento, conservadas en el servidor.
- Las prácticas y exámenes tienen pesos configurables; el examen debe pesar más. Los porcentajes concretos deben aprobarse con el docente.
- Las entregas calificadas conservan la retroalimentación docente. Las nuevas notas usan escala de 0 a 20.
- Los registros de investigación pretest y postest se deben identificar por separado: sus diez ítems de observación no equivalen automáticamente a las notas de la aplicación.

La política implementada toma el último intento de cada práctica o examen identificado para el promedio y conserva su historial. El docente debe validar esta elección antes de utilizar la libreta con fines oficiales. También quedan por precisar las ausencias, recuperaciones y cierre formal de bimestre.

## Relación con aplicación, datos y tecnología

Flask presta los servicios de aprendizaje, evaluación, notas y administración. PostgreSQL conserva usuarios, materiales, versiones de intentos, respuestas, resultados y permisos de reapertura. Los proveedores de IA generan borradores de contenido; no deciden por sí solos las reglas académicas ni recalifican una respuesta ya enviada. En la demostración gratuita, los archivos pequeños también se conservan en PostgreSQL para soportar el disco efímero del alojamiento.

El despliegue propuesto separa el navegador, la aplicación web, la base de datos y el proveedor externo de IA. El modelo predictivo se mantiene como apoyo al seguimiento y debe distinguir explícitamente el benchmark de cualquier validación futura con datos institucionales.

## Brechas y aceptación

| Brecha observada | Cambio | Evidencia de aceptación |
| --- | --- | --- |
| Juegos mezclados con notas | Separar entrenamiento y evaluación | Repetir juegos no cambia la libreta |
| Preguntas regeneradas al calificar | Congelar preguntas por intento | Respuesta calificada contra la misma versión |
| Examen sin control de repetición | Intento único y reapertura docente | Segundo intento bloqueado y reapertura registrada |
| Operación dependiente de equipo local | Publicar aplicación y persistencia remota | Dos laptops acceden a una URL y comparten datos |
| Espera de IA durante actividad del alumno | Preparar y guardar contenido | Prácticas y exámenes funcionan sin API disponible |
| Nota sin regla de ponderación | Configurar pesos | Examen pesa más y se muestra nota pendiente si falta evidencia |

Esta propuesta usa capacidades, actores, información, reglas y brechas para describir el negocio educativo. El diagrama técnico de carpetas o servidores debe presentarse como otra vista, relacionada con este proceso. Referencia del marco: [The Open Group sobre TOGAF](https://help.opengroup.org/hc/en-us/articles/32726995273362-Understanding-the-TOGAF-Standard).
