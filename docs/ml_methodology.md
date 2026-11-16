# Metodología del modelo de referencia

Revisión del 16 de noviembre de 2026. El modelo es una referencia técnica de secundaria; no está validado para alumnos de primaria de este colegio. El historial real disponible contiene solo quince registros literales del primer bimestre de cuarto. Esos registros no se convierten a números ni se usan para inventar una validación temporal.

## Procedencia y adaptación

Se descarga el archivo oficial de [UCI Student Performance](https://archive.ics.uci.edu/dataset/320/student-performance), creado por Paulo Cortez, DOI 10.24432/C5TG7T, bajo licencia CC BY 4.0. Se utiliza únicamente student-por.csv: 649 observaciones. Se evita concatenar cursos con identificadores distintos para un mismo alumno.

G1 y G2 son notas de periodos anteriores; G3 es la nota final. Se usan G1 y G2 como entradas y G3 para definir el resultado. El adaptador asigna fechas artificiales del año 2000 exclusivamente para expresar el orden de esos eventos. No son fechas de recolección ni cohortes longitudinales reales.

La etiqueta de esta referencia es G3 menor que 11. Es una convención de este experimento, no una equivalencia oficial de AD/A/B/C ni una regla normativa de aprobación para primaria. El historial literal del colegio sigue separado.

La procedencia conserva URL, curso, número de observaciones, licencia y huellas SHA256 del archivo descargado, del CSV original y de los eventos adaptados. El entrenamiento comprueba la huella del archivo de eventos antes de continuar.

## Separación para selección y prueba

1. Partición exterior por alumno con semilla 42: 486 observaciones de entrenamiento y 163 de prueba. No hay alumnos compartidos entre ambos conjuntos.
2. Selección dentro del entrenamiento mediante tres pliegues estratificados, separados por alumno. Cada pliegue tiene 324 observaciones para ajustar y 162 para validar.
3. Comparación de LogisticRegression, DecisionTree, RandomForest y GradientBoosting. Se prioriza sensibilidad, luego F1, AUC y exactitud de la validación interna.
4. Ajuste del algoritmo seleccionado con las 486 observaciones exteriores de entrenamiento.
5. Evaluación final del seleccionado sobre las 163 observaciones reservadas. La prueba final no decide cuál candidato gana.

El preprocesamiento se ajusta dentro de cada Pipeline y de cada pliegue. La selección no recibe la partición final. La implementación se encuentra en ml/pipeline/trainer.py; el comando histórico ml/scripts/train.py delega al mismo protocolo.

La referencia no admite presentarse como evaluación temporal aunque se solicite esa opción: utiliza separación por alumno. Una validación institucional temporal exige periodos reales anteriores y posteriores con resultados verificables; si no existen, se rechaza esa partición en vez de entrenar con un periodo futuro.

## Resultado observado

Modelo seleccionado: DecisionTree, versión v1_20261116. En la prueba final: exactitud 0.9018, sensibilidad 0.8049, F1 de riesgo 0.8049 y AUC 0.9193. Las métricas de comparación de los cuatro candidatos son de validación interna y se muestran por separado.

Estas cifras son resultados de una partición del benchmark, sin intervalo de incertidumbre ni validación externa. No prueban calibración de probabilidades, precisión institucional ni mejora del aprendizaje. Una probabilidad de 100 % en una hoja del árbol no constituye certeza sobre un alumno.

La antigua cifra de sensibilidad 90.48 % procedía de otro protocolo y otro conjunto: el script anterior inventaba etiquetas 2023/2024 y elegía candidatos con el mismo conjunto que reportaba. No se conserva como estimación independiente ni se compara directamente con esta revisión.

## Variables y control de calidad

Se comparte una única extracción de 18 variables entre entrenamiento e inferencia, en ml/pipeline/feature_builder.py. El esquema incluye resúmenes de notas, frecuencia, aciertos, tiempos, materiales y entregas. En UCI solo hay G1 y G2 para estas entradas; muchas variables de telemetría quedan constantes. El modelo de referencia no demuestra que esas variables ausentes sean útiles en el colegio.

Una fecha de corte inválida se rechaza. Con corte explícito, un evento sin fecha válida se excluye; una fecha sin hora incluye el día completo. Las fechas con zona se normalizan a UTC. Las notas numéricas inválidas o ausentes y los objetivos desconocidos se rechazan, sin convertirlos silenciosamente en cero o en alumno aprobado. No se infiere el perfil académico desde una nota aislada sin identificar al alumno.

La falta de historial devuelve estado explícito y probabilidad nula. Los fallos de datos y de modelo no se sustituyen por porcentajes fijos. Los identificadores no entran en la matriz predictiva; esto por sí solo no constituye una auditoría de privacidad ni acredita anonimización irreversible.

El constructor actual admite una observación por alumno. Rechaza mezclar años, periodos o cursos de una misma persona, objetivos contradictorios y observaciones sin notas previas al corte. Una futura preparación longitudinal requiere definir observaciones, cortes y resultados posteriores de forma explícita; este constructor no los infiere. La ejecución institucional exige `--cutoff-date`, sin reutilizar una fecha histórica predeterminada. La API por alumno conserva el alcance y el aviso del modelo de referencia.

## Reproducción

```powershell
python ml/scripts/download_and_prepare_benchmark.py
python ml/run_pipeline.py --source benchmark --split-strategy group
```

Los comandos regeneran artefactos de referencia. No deben ejecutarse como si entrenaran un modelo institucional. Para el colegio se necesitan datos autorizados, objetivo y corte definidos, cobertura de casos y evaluación posterior independiente.

Referencias técnicas: [UCI](https://archive.ics.uci.edu/dataset/320/student-performance), [validación en scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html) y [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html).
