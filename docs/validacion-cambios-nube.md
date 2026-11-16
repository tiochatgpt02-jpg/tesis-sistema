# Validación técnica de la revisión

Revisión del 15 de noviembre de 2026. Las comprobaciones son técnicas y no constituyen una nueva intervención humana con alumnos. Informes privados se conservan fuera de GitHub.

## Evidencia obtenida

- Batería local: 203 pruebas aprobadas y tres integraciones de nube omitidas por defecto. El adaptador Windows de directorios temporales no modifica las reglas de negocio probadas.
- PostgreSQL real: test_real_literal_history_auto_assessments_and_frozen_closure aprobado en esquema desechable. Migraciones aplicadas dos veces, importación idempotente, notas automáticas, promedio 17.60, rechazo de examen manual, cierre congelado, cambio de pesos y reapertura auditable.
- Registro autorizado: quince alumnos de cuarto y primer bimestre 2026, coincidencia exacta con padrón y fórmulas verificadas. No se crearon notas numéricas desde AD/A/B/C.
- Edge: ocho editores visuales, etiquetas, eliminación de alternativa correcta, práctica con notas 20 y 0, examen con 20 y segundo intento bloqueado. El harness activa el contenedor de evaluación para probar componentes con datos ficticios; no se presenta como un recorrido humano completo de navegación.
- Groq real desde TEORIA_2.pptx para quinto: extracción 0.024 s y generación 1.088 s. Una llamada, sin modificar notas. Se contrastó SMARTART con el material. No garantiza latencia futura.

## Seis sesiones antes de la revisión

Seis sesiones HTTP independientes, dos rondas, commit bd09126a653e356189369ba3e4fae69c2ea7ba5d, sin modificar notas ni llamar a IA.

| Operación | Solicitudes | Mediana segundos | P95 observado | Errores |
| --- | --- | --- | --- | --- |
| Panel alumno | 12 | 1.179 | 1.369 | 0 |
| Login con primera redirección | 6 | 8.020 | 8.140 | 0 |
| Progreso | 12 | 0.289 | 0.312 | 0 |
| Riesgo | 12 | 0.172 | 0.372 | 0 |

Despertar inicial: 53.102 s. El login incluye autenticación y primera carga. Se elimina una lectura redundante del perfil y se reutiliza durante cada petición; no se reduce la seguridad del hash. La comparación posterior figura a continuación; dos mediciones no permiten atribuir causalmente sus diferencias a una sola optimización.

Los percentiles son de una muestra pequeña de peticiones; no son Core Web Vitals de campo ni prueban 51 usuarios simultáneos. No hay medición de campo p75 de LCP, INP y CLS. Referencia: https://web.dev/articles/vitals.

## Pendientes externos

Solo hay un bimestre literal. Su nota final es la moda de los cinco indicadores con desempate por orden; no permite demostrar predicción futura. El benchmark sigue identificado como referencia.

Se conocen límites anuales del 20 de marzo al 18 de diciembre; faltan cortes interiores confirmados, material oficial por grado, piloto humano con evidencia y aceptación académica. Documentar estos hitos no los completa.

Render Free puede suspenderse y su disco es efímero; los datos persisten en PostgreSQL externo. Restricciones: https://render.com/docs/free. La versión activa debe contrastarse con el SHA remoto en la verificación de publicación; cambios locales no implican despliegue terminado.


## Comprobación posterior en la publicación 712ad71

Seis sesiones, mismo tipo de carga y ninguna nota real modificada. Panel: mediana 1.354 s y P95 1.459 s; login con primera redirección: 6.880 s y 7.005 s; progreso: 0.323 s y 0.412 s; riesgo: 0.179 s y 0.239 s. Cero errores en las 42 peticiones. La mediana del login disminuyó, mientras la del panel aumentó 0.175 s: no se afirma una mejora uniforme ni causal.

La web publicada verificó conexión PostgreSQL, roles, acceso al historial propio y bloqueo ajeno, dos prácticas y un examen con calificación, persistencia y reapertura. Las evaluaciones y resultados temporales de la cuenta ficticia se limpiaron. Un juego real desde el PPT de SmartArt se generó en 1.110 s y respondió al jugar en 0.150 s; se comprobó que no añadió notas y se eliminó la prueba temporal.

## Revisión metodológica del 16 de noviembre

La cifra antigua de sensibilidad del benchmark no era una evaluación independiente de la selección: se reemplaza por el protocolo y artefactos descritos en [metodología](ml_methodology.md). Un único curso UCI oficial, 486 observaciones de entrenamiento y 163 de prueba; elección por validación interna sin acceso al test. La sensibilidad final observada es 80.49 %, no una promesa para este colegio.

El usuario autorizó fechas referenciales mientras consigue las del colegio. Se usan los bloques lectivos de [MINEDU 2026](https://cdn.www.gob.pe/uploads/document/file/9529291/7799833-orientaciones-para-el-inicio-del-ano-escolar-2026.pdf), adaptando el primer inicio al 20 de marzo. Permanecen sin confirmar y no sustituyen el calendario aprobado de la institución.
