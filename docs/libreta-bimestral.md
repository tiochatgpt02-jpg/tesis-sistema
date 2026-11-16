# Libreta bimestral

Pesos: tareas 10 %, participación 10 %, libro 10 %, práctica 1 10 %, práctica 2 10 % y examen 50 %. Suman 100 %. Las notas nuevas usan escala 0 a 20.

Promedio: `0.10*tareas + 0.10*participación + 0.10*libro + 0.10*práctica1 + 0.10*práctica2 + 0.50*examen`, redondeado a dos decimales. Con 10, 12, 14, 16, 18 y 20 resulta 17.00. Con 10, 12, 14, 20, 20 y 20 resulta 17.60. Una nota ausente deja el resultado pendiente; cero cuenta como nota.

## Registro docente

1. Revisar y publicar prácticas y examen del grado.
2. Abrir Reportes y Registrar notas bimestrales; elegir grado, año y bimestre.
3. Vincular explícitamente dos prácticas diferentes y un examen. No se deducen por orden de creación.
4. Registrar solo tareas, participación y libro. Prácticas y examen son siempre automáticos, incluso cuando falta el vínculo.
5. El alumno resuelve las evaluaciones; la libreta recoge el último resultado del periodo. Los intentos anteriores se conservan.
6. Revisar calendario y pendientes antes de cerrar. El cierre congela notas, pesos y fechas. La reapertura conserva motivo y actor.

Las prácticas admiten repetición. El examen tiene treinta minutos desde Comenzar, un intento y recuperación autorizada por el docente. Una edición posterior vuelve la evaluación a revisión; el intento ya iniciado conserva preguntas y claves originales.

Las fechas se editan en /teacher/academic-calendar. Se comunicaron inicio anual 20 de marzo y fin 18 de diciembre de 2026; los cortes interiores siguen provisionales. No se debe confirmar el calendario sin aceptación del colegio. El cierre exige confirmación.

Los juegos no aportan calificaciones. Las ausencias quedan pendientes mientras no haya regla académica aprobada. Reportes y Excel usan las mismas reglas de la libreta. El historial AD/A/B/C se consulta separado, sin transformación a escala numérica.

## Implementación

services/grading_policy_service.py calcula pesos; bimester_grade_service.py vincula fuentes y notas; academic_calendar_service.py aplica fechas; academic_closure_service.py congela cierres; learning_attempt_service.py califica preguntas congeladas.

Las pruebas test_bimester_gradebook.py, test_assessment_kinds.py, test_academic_closure.py y test_postgres_release_20261115.py verifican ponderación, permisos, repetición, persistencia y cierre.
