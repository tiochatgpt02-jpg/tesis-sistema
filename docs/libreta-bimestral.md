# Libreta bimestral del piloto

Distribución indicada por el usuario el 14 de noviembre de 2026:

| Componente | Peso |
| --- | --- |
| Revisión de tareas | 10 % |
| Participación | 10 % |
| Revisión del libro | 10 % |
| Práctica 1 | 10 % |
| Práctica 2 | 10 % |
| Examen bimestral | 50 % |

Todas las notas se registran en escala de 0 a 20. El promedio es
`0.10*tareas + 0.10*participación + 0.10*libro + 0.10*práctica1 + 0.10*práctica2 + 0.50*examen`.
El resultado se redondea a dos decimales. Con notas 10, 12, 14, 16, 18 y 20, el promedio es 17.
Una casilla vacía mantiene la nota final pendiente; cero es una nota válida. Los juegos no participan en el cálculo.

## Registro docente

En Reportes, abrir **Registrar notas bimestrales** y seleccionar grado, año y bimestre.
Escribir las notas y guardar cada fila. Los registros están separados por alumno, año y bimestre.
Vaciar una casilla y guardar elimina esa nota manual. El servidor valida los valores y el rol docente.

En **Vincular prácticas y examen del sistema**, el docente puede asignar una fuente distinta a cada práctica y una evaluación al examen.
La fuente debe pertenecer al grado seleccionado. Los componentes vinculados usan el último resultado del alumno en ese periodo,
se muestran como automáticos y no admiten edición manual mientras exista el vínculo.
No se asigna automáticamente una práctica a "práctica 1" o "práctica 2" por su orden de creación.
Sin vínculo, las seis notas admiten registro manual. Cambiar la fuente no elimina los intentos originales.

La vinculación utiliza los intervalos ya definidos en los reportes: bimestre 1 de marzo a mayo, 2 de junio a julio,
3 de agosto a octubre y 4 de noviembre a diciembre. El formulario muestra las fechas aplicadas; deben contrastarse
con el calendario real del colegio antes de usarlo como registro oficial.

Los porcentajes pueden consultarse en **Reglas de calificación**. Deben sumar 100; el examen debe pesar más que cada otro componente individual.
Los reportes y la exportación Excel calculan el mismo promedio a partir de los componentes del bimestre.
El panel del alumno muestra la nota ponderada del bimestre actual. Los registros anteriores de actividades y sus intentos se conservan.

## Implementación y verificación

- `services/grading_policy_service.py`: validación de porcentajes y cálculo decimal.
- `services/bimester_grade_service.py`: notas manuales, fuentes y aislamiento por periodo.
- `views/bimester_grades.html`: registro docente accesible, sin edición de JSON.
- `sql/migrations/postgresql/20261114_grading_components.sql`: migración aditiva, repetible y sin importación de notas.
- `test_six_weights_apply_exam_50_and_five_components_10`: fórmula acordada.
- `test_missing_grade_is_pending_but_zero_is_a_real_grade`: pendientes y cero.
- `test_manual_marks_preserve_year_period_student_and_validate_atomically`: separación y validación.
- `test_linked_practice_uses_latest_in_term_and_cannot_be_overwritten_manually`: vinculación.
- `test_report_and_excel_have_same_six_component_average_and_period`: coherencia del reporte y Excel.
- `test_teacher_can_save_six_marks_and_student_cannot_modify_gradebook`: permisos y guardado.
- `test_six_component_gradebook_persists_and_links_real_results`: PostgreSQL real en esquema temporal aislado.
