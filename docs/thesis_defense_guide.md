# Preguntas para la sustentación

## Qué está implementado

La aplicación publicada usa Flask y PostgreSQL en Neon. Groq genera borradores desde el material docente; el alumno usa contenido guardado. El sistema conserva intentos y califica preguntas congeladas. La libreta tiene pesos 10/10/10/10/10/50; las prácticas y el examen se vinculan expresamente y sus notas son automáticas.

## Qué tipo de arquitectura tiene

Es un monolito modular con controladores, servicios, presentación y persistencia. La adaptación de TOGAF 9.2 organiza visión, actores, procesos, datos, aplicaciones, tecnología, brechas y gobierno. No se afirma certificación ni que todo el desarrollo original haya seguido TOGAF desde el inicio. Consultar [expediente](arquitectura-togaf-9-2.md).

## Dónde está el Machine Learning

El entrenamiento está en ml/run_pipeline.py y ml/pipeline/trainer.py. La inferencia está en ml/pipeline/predictor.py y services/ml/prediction_service.py. El registro carga el artefacto y el extractor compartido obtiene variables del historial. Generar un juego con Groq es otra función y no constituye entrenar ese modelo.

## Qué tan preciso es

El benchmark revisado seleccionó DecisionTree mediante validación interna del entrenamiento. En 163 observaciones reservadas tuvo exactitud 90.18 % y sensibilidad 80.49 %. Son resultados de una referencia pública de secundaria, no precisión del colegio. No se promete una cifra superior ni una probabilidad específica para la demostración. [Método y limitaciones](ml_methodology.md).

## Por qué no se entrenó con el registro del colegio

Solo se proporcionó un bimestre literal de quince alumnos de cuarto. La nota final de ese archivo se deriva de los cinco indicadores del mismo periodo. Usarlos para predecir ese mismo resultado no demostraría anticipación. Se importaron sin convertirlos a números; faltan resultados posteriores para una validación temporal institucional.

No se sostienen las afirmaciones antiguas de que todos los datos del colegio eran monoclase, tenían desplazamientos o estaban alterados: no hay evidencia suficiente para atribuir esas características al archivo entregado.

## Qué significa una probabilidad

Es la salida del modelo para sus entradas y entrenamiento. No es certeza matemática sobre una persona, no demuestra causalidad y no se ha calibrado con alumnos del colegio. El docente debe contrastarla con evidencia académica y el aviso de origen del modelo.

## Cómo se evita mezclar evaluación y selección

El algoritmo se elige utilizando solo pliegues del entrenamiento. El conjunto final separado se usa después de esa elección. Las fechas de la adaptación UCI son artificiales, no cohortes reales; se usa partición por alumno. La evaluación temporal del colegio sigue pendiente. No se garantiza ausencia universal de fuga por tener un Pipeline: también se revisan objetivo, fechas, variables y participantes.

## Cómo se protegen los datos

Hay contraseñas con hash, control por roles, consultas del historial propio y separación de secretos y archivos personales del repositorio público. Estas medidas describen el producto; no constituyen una auditoría legal ni prueban anonimización irreversible. El colegio debe definir acceso, respaldo, conservación y autorizaciones de uso.

## Qué demuestran las pruebas

Demuestran los comportamientos específicos verificados en código, base y navegador. No demuestran por sí solas aprendizaje, aceptación de alumnos reales, cobertura completa o cumplimiento institucional. El padrón de 51 cuentas, las notas de quince alumnos y las mediciones pretest/postest son conjuntos diferentes.

Para exponer, seguir la [guía del jurado](guia_demostracion_jurado.md) y explicar los pendientes en [protocolo de piloto](protocolo-piloto.md).
