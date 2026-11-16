#!/usr/bin/env python3
"""Comando único y orquestador integral del pipeline de Machine Learning escolar.

Ejecuta el ciclo de vida completo de ML de forma reproducible:
  1. Ingesta y validación rigurosa de datos crudos (data_loader)
  2. Extracción de variables con aislamiento temporal anti-leakage (feature_builder)
  3. Entrenamiento y comparación de 4 familias supervisadas (trainer)
  4. Evaluación diagnóstica, matriz de confusión y explicabilidad (evaluator & predictor)

Uso:
  python ml/run_pipeline.py [--source {benchmark,institutional}] [--split-strategy {temporal,group}]
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import Config
from ml.pipeline.data_loader import load_raw_csv
from ml.pipeline.feature_builder import build_processed_matrix
from ml.pipeline.trainer import train_candidate_models
from ml.pipeline.predictor import AcademicRiskPredictor


def run_ml_pipeline(
    source: str = 'benchmark',
    split_strategy: str = 'temporal',
    cutoff_date: str = '2024-04-30',
    verbose: bool = True,
    output_root: Path | None = None,
) -> Dict[str, Any]:
    """Ejecuta el pipeline integral paso a paso con trazabilidad total."""
    start_time = time.time()
    source_clean = source.strip().lower()

    print("=" * 75)
    print("      SISTEMA IA - ORQUESTADOR DEL PIPELINE DE MACHINE LEARNING")
    print("=" * 75)
    print(f"Modo de Dataset:      {source_clean.upper()}")
    print(f"Estrategia de Split:  {split_strategy.upper()}")
    print(f"Fecha de Corte:       {cutoff_date}")
    print(f"Inicio de Ejecución:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 75)

    # 1. Rutas de directorios
    raw_dir = ROOT / "ml" / "datasets" / source_clean / "raw"
    artifact_root = Path(output_root).resolve() if output_root is not None else ROOT / 'ml'
    processed_dir = artifact_root / "datasets" / source_clean / "processed"
    models_dir = artifact_root / "models" / source_clean

    # Identificar archivo fuente
    if source_clean == 'benchmark':
        raw_csv = raw_dir / "uci_student_performance_institutional.csv"
        if not raw_csv.is_file():
            # Fallback a ubicación previa
            legacy_raw = ROOT / "ml" / "datasets" / "raw" / "uci_student_performance_institutional.csv"
            if legacy_raw.is_file():
                raw_csv = legacy_raw
    else:
        raw_csv = raw_dir / "school_academic_history.csv"

    if not raw_csv.is_file():
        raise FileNotFoundError(
            f"No se encontró el dataset crudo en: {raw_csv}\n"
            f"Para el entorno '{source_clean}', debe importar primero los datos utilizando:\n"
            f"  python ml/scripts/import_school_dataset.py --input <archivo.csv>"
        )

    # -------------------------------------------------------------
    # PASO 1: Ingesta y Validación de Datos
    # -------------------------------------------------------------
    print("\n[PASO 1/4] Validando esquema y calidad de datos crudos...")
    records, quality_report = load_raw_csv(raw_csv)
    print(f"  -> Archivo verificado:      {raw_csv.name}")
    print(f"  -> Total filas analizadas:  {quality_report['total_rows_read']}")
    print(f"  -> Registros válidos:       {quality_report['valid_events']}")
    print(f"  -> Alumnos únicos:          {quality_report['unique_students']}")
    print(f"  -> Filas descartadas:       {quality_report['invalid_rows']}")

    # -------------------------------------------------------------
    # PASO 2: Extracción de Variables con Filtro Anti-Leakage
    # -------------------------------------------------------------
    print("\n[PASO 2/4] Construyendo matriz de características (anti-leakage)...")
    processed_csv = processed_dir / "training_dataset.csv"
    features_json = processed_dir / "features.json"

    n_samples = build_processed_matrix(
        source_csv=raw_csv,
        output_csv=processed_csv,
        cutoff_date=cutoff_date,
        features_json_path=features_json,
    )
    print(f"  -> Matriz procesada:        {processed_csv}")
    print(f"  -> Observaciones generadas: {n_samples}")
    print(f"  -> Esquema serializado en:  {features_json.name} (18 variables canónicas)")

    # -------------------------------------------------------------
    # PASO 3: Entrenamiento Multialgorítmico y Selección
    # -------------------------------------------------------------
    print("\n[PASO 3/4] Entrenando y comparando familias de algoritmos supervisados...")
    training_summary = train_candidate_models(
        dataset_path=processed_csv,
        output_model_dir=models_dir,
        split_strategy=split_strategy,
        dataset_name=source_clean,
    )

    best_name = training_summary.get('selected_algorithm', 'Desconocido')
    test_metrics = training_summary.get('test_metrics', {})
    val_info = training_summary.get('validation_info', {})

    print(f"  -> Algoritmo Ganador:       {best_name}")
    print(f"  -> Exactitud (Accuracy):    {test_metrics.get('accuracy', 0.0) * 100:.2f}%")
    print(f"  -> Sensibilidad (Recall):   {test_metrics.get('positive_class_recall', 0.0) * 100:.2f}%")
    print(f"  -> F1-Score (Riesgo):       {test_metrics.get('positive_class_f1', 0.0):.4f}")
    if test_metrics.get('roc_auc') is not None:
        print(f"  -> ROC-AUC:                 {test_metrics.get('roc_auc', 0.0):.4f}")
    print(f"  -> Artefacto serializado:   {models_dir / 'model.joblib'}")

    # -------------------------------------------------------------
    # PASO 4: Verificación de Inferencia y Explicabilidad
    # -------------------------------------------------------------
    print("\n[PASO 4/4] Verificando motor de inferencia y explicabilidad pedagógica...")
    predictor = AcademicRiskPredictor(model_dir=models_dir)
    if not predictor.is_available():
        raise RuntimeError("El modelo generado no pudo ser verificado por el predictor.")

    # Diagnóstico con perfil de riesgo sintomático
    sample_risk_features = {
        'total_attempts': 2,
        'evaluation_count': 1,
        'activities_count': 1,
        'average_score': 6.0,
        'average_evaluation_score': 5.5,
        'last_score': 5.0,
        'score_trend': -1.0,
    }
    diag_res = predictor.predict(sample_risk_features)
    print("  -> Diagnóstico de prueba (Perfil con notas < 11.0):")
    print(f"     Nivel de Riesgo:     {diag_res.get('risk_level')} ({diag_res.get('prediction', {}).get('risk_level')})")
    print(f"     Probabilidad:        {diag_res.get('risk_probability') * 100:.1f}%")
    print("     Factores explicables detectados:")
    for f in diag_res.get('main_factors', []):
        print(f"       - {f}")

    # Sincronizar directorio de modelo raíz si es benchmark (para retrocompatibilidad)
    if source_clean == 'benchmark' and output_root is None:
        import joblib
        root_model_joblib = ROOT / "ml" / "models" / "student_risk_pipeline.joblib"
        root_metadata = ROOT / "ml" / "models" / "metadata.json"
        try:
            joblib.dump(predictor.get_model(), root_model_joblib)
            import shutil
            shutil.copy2(models_dir / "metadata.json", root_metadata)
        except Exception:
            pass

    elapsed = time.time() - start_time
    print("-" * 75)
    print(f"PIPELINE COMPLETADO EXITOSAMENTE en {elapsed:.2f} segundos.")
    print("=" * 75)

    return {
        'source': source_clean,
        'selected_algorithm': best_name,
        'test_metrics': test_metrics,
        'validation_info': val_info,
        'elapsed_seconds': round(elapsed, 2),
    }


def main():
    default_source = getattr(Config, 'ML_DATASET_SOURCE', 'benchmark')

    parser = argparse.ArgumentParser(
        description="Comando único de ejecución del pipeline de Machine Learning escolar."
    )
    parser.add_argument(
        "--source",
        choices=["benchmark", "institutional"],
        default=default_source,
        help=f"Fuente del dataset a procesar y entrenar (default: '{default_source}').",
    )
    parser.add_argument(
        "--split-strategy",
        choices=["temporal", "group"],
        default="temporal",
        help="Estrategia de evaluación: 'temporal' (inter-año) o 'group' (por estudiante).",
    )
    parser.add_argument(
        "--cutoff-date",
        type=str,
        default="2024-04-30",
        help="Fecha de corte anti-leakage (YYYY-MM-DD).",
    )
    args = parser.parse_args()

    try:
        run_ml_pipeline(
            source=args.source,
            split_strategy=args.split_strategy,
            cutoff_date=args.cutoff_date,
        )
    except Exception as exc:
        print(f"\n[ERROR CRÍTICO] El pipeline se interrumpió: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
