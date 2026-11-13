# Validación de los cambios para despliegue

Fecha: 13 de noviembre de 2026. Estado: cambios locales preparados; aplicación todavía sin publicar.

La ejecución completa terminó con **149 pruebas aprobadas y 1 omitida**. También pasaron la compilación sintáctica de Python, `node --check` sobre los tres archivos JavaScript modificados y `git diff --check`. Se comprobaron las páginas docente, alumno y configuración mediante el cliente de Flask, con respuesta HTTP 200.

Actualización posterior: al configurar `DATABASE_URL`, la conexión a Neon y el uso de TLS desde el cliente quedaron confirmados. La prueba antes omitida se ejecutó por separado y pasó contra PostgreSQL real. La simulación ampliada duró 55,90 segundos, incluyendo creación de esquema, migraciones, conexiones, verificaciones y limpieza; este total no representa la latencia de una actividad en el sitio desplegado. Se corrigió el aislamiento de la prueba para usar `SET LOCAL search_path` dentro de la transacción, ya que el endpoint pooled de Neon rechaza ese parámetro durante el inicio de conexión.

La simulación verificó práctica de 10 y repetición de 20, examen de 20 con bloqueo posterior, reapertura docente y segundo examen de 0 intencional, tres partidas sin notas nuevas, seis reenvíos concurrentes sin duplicados y recuperación de un archivo desde otra conexión. Usó preguntas predefinidas, no generación de IA. Todos los datos se crearon en un esquema temporal y se confirmó que no quedó ningún esquema de esa prueba. El informe sanitizado está en `audit/simulacion-neon.json` y la ejecución en `audit/neon-simulation.xml`, fuera del repositorio de la aplicación.

El entorno de pruebas usa datos ficticios aislados por caso. Los temporales se ubicaron en el espacio de trabajo mediante un adaptador de ejecución porque el aislamiento de Windows bloquea los directorios temporales privados creados por pytest. El resultado estructurado de la ejecución queda en `audit/full-suite.xml`, fuera del repositorio de la aplicación. Las pruebas heredadas que escriben artefactos ML modifican archivos de trabajo; después de ejecutarlas se restauraron los cuatro artefactos afectados a su estado inicial. No se entrega un modelo reentrenado como parte de este cambio.

## Evidencia por comportamiento

| Comportamiento | Prueba o archivo de evidencia |
| --- | --- |
| Groq utiliza el endpoint configurado y una espera limitada | `test_groq_request_and_bounded_timeout` |
| NVIDIA es una opción explícita sin encadenar solicitudes | `test_nvidia_is_explicit_not_an_automatic_extra_wait` |
| Los errores de cuota no exponen claves ni el cuerpo del proveedor | `test_rate_limit_does_not_expose_provider_body_or_key` |
| Las peticiones de alumnos no llaman al modelo externo | `test_student_request_never_calls_external_model` |
| Las prácticas califican la versión original y verifican pertenencia del intento | `test_frozen_practice_exact_grading_idempotency_and_ownership` |
| El examen se reanuda, limita intentos y permite reapertura | `test_exam_resume_single_attempt_and_teacher_reopening` |
| Los intentos vencidos o cerrados no se vuelven a enviar | `test_expired_exam_rejects_submission_and_reopening_closes_old_attempt` |
| Los juegos no inflan el promedio | `test_games_do_not_inflate_grade_and_overview_is_mean` |
| Tampoco los juegos antiguos escriben calificaciones nuevas | `test_legacy_game_result_never_writes_an_academic_note` |
| El reporte respeta el bimestre | `test_report_excludes_other_bimesters` |
| La ponderación toma el último intento identificado y deja pendiente una categoría ausente | `test_weights_use_latest_practice_and_missing_exam_remains_pending` |
| Los reportes docentes requieren la sesión y rol correctos | `test_teacher_endpoints_reject_anonymous_and_students` |
| El examen no entrega claves y utiliza el intento emitido por el servidor | `test_published_exam_has_no_answer_keys_and_post_uses_server_attempt` |
| La práctica de una presentación conserva el origen y no regenera al enviar | `test_material_practice_keeps_presentation_source_and_does_not_regenerate` |
| Seis envíos concurrentes del mismo intento guardan una nota en el almacén simulado | `test_six_simultaneous_submissions_record_one_grade` |
| La entrega docente usa nota vigesimal y porcentaje correspondiente | `test_review_submission_updates_student_notes_for_gradebook` |
| Configuración de alojamiento, conexión y requisitos de ejecución | `render.yaml`, `requirements-runtime.txt`, `scripts/setup_db.py` |

Las primeras quince pruebas de la tabla están en `tests/test_cloud_workflows.py`; la prueba de entregas está en `tests/test_teacher_submission_review.py`. La concurrencia verificada aquí es la integridad de seis envíos al almacén simulado, no una medición de carga de la aplicación alojada.

## Comprobaciones aún pendientes

- La prueba `test_persisted_exam_is_atomic_idempotent_and_reopens_without_losing_history` ya pasó contra Neon en la actualización descrita arriba. Aún queda verificar la conservación de datos después de reiniciar el hosting desplegado.
- La clave de Groq está presente en la configuración local, sin imprimirse. La llamada real de prueba no pudo conectar desde el entorno de ejecución. No se certifica su validez ni se publican cifras de latencia.
- El navegador automatizado informó que su host no está disponible. Quedan pendientes la revisión visual, arrastrar y soltar en los juegos y el recorrido completo en las dos laptops.
- El conector de GitHub autenticado como `ZaydAyasta` recibió HTTP 404 para `xpachecosa-stack/sistema-IA`. No se han subido los cambios ni creado una URL pública. Hay que habilitar acceso al repositorio o acordar otro destino.
- `DATABASE_URL` ya está configurada y verificada. Falta publicar el servicio gratuito de hosting y comprobar inicio de sesión, generación docente, notas y archivos conservados tras reinicio y acceso simultáneo desde las laptops.

La preparación y los límites del alojamiento gratuito se explican en [la guía de despliegue](despliegue-gratuito.md).
