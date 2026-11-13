#!/usr/bin/env python3
"""Script reproducible de entrenamiento y selección de modelos supervisados para riesgo académico.

Compara: LogisticRegression, DecisionTreeClassifier, RandomForestClassifier.
Soporta dos estrategias de evaluación rigurosas:
  1. Temporal holdout (por año/periodo académico): entrena en periodos pasados y evalúa en el último periodo.
  2. GroupShuffleSplit (por student_id): garantiza que un estudiante no se repita entre train y test.

Garantía estricta de seguridad/privacidad:
  Los identificadores (student_id, student_code) y metadatos se usan única y exclusivamente
  para vinculación y partición de datos. NUNCA ingresan a la matriz de características predictivas X.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from ml.scripts.evaluate import compute_classification_metrics
from services.ml.model_registry import ModelRegistry

DISALLOWED_IN_X = {
    'student_id', 'student_code', 'id', 'user_id', 'codigo_estudiante', 'dni',
    'first_name', 'last_name', 'email', 'phone', 'academic_year', 'period',
    'academic_period', 'cutoff_date', 'target_risk', 'target', 'risk_level'
}


def load_dataset(csv_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str], List[Dict[str, Any]]]:
    """Carga la matriz de datos, extrae metadatos y asegura la exclusión estricta de identificadores de X."""
    import csv

    if not csv_path.is_file():
        raise FileNotFoundError(f"Archivo de dataset no encontrado: {csv_path}")

    rows = []
    with csv_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("El archivo de dataset no contiene columnas.")
        for r in reader:
            rows.append(r)

    if not rows:
        raise ValueError("El dataset está vacío (0 observaciones).")

    # 1. Extraer columnas predictivas canónicas presentes en el CSV
    feature_cols = [
        col for col in ModelRegistry.DEFAULT_FEATURE_NAMES
        if col in rows[0] and col.lower() not in DISALLOWED_IN_X
    ]
    if not feature_cols:
        raise ValueError("No se encontraron columnas predictivas reconocidas en el dataset.")

    # 2. Verificación estricta anti-leaks de identificadores
    for col in feature_cols:
        col_lower = col.lower()
        if col_lower in DISALLOWED_IN_X or 'student' in col_lower or 'codigo' in col_lower:
            raise ValueError(
                f"Violación crítica de integridad: La columna '{col}' es un identificador o metadato "
                "y bajo ninguna circunstancia debe ingresar a la matriz de entrenamiento X."
            )

    assert 'student_id' not in feature_cols, "student_id NUNCA debe estar en feature_cols"
    assert 'student_code' not in feature_cols, "student_code NUNCA debe estar en feature_cols"

    X = []
    y = []
    groups = []
    metadata = []

    for r in rows:
        features = []
        for col in feature_cols:
            val = r.get(col)
            if val is None or str(val).strip() == '' or str(val).strip().lower() == 'nan':
                features.append(np.nan)
            else:
                try:
                    features.append(float(str(val).strip()))
                except ValueError:
                    features.append(np.nan)

        target = int(float(r.get('target_risk', 0) or 0))
        group = int(float(r.get('student_id', 0) or 0))

        # Construir identificador representativo del periodo
        year = r.get('academic_year')
        per = r.get('period')
        acad_per = r.get('academic_period')
        if not acad_per:
            if year and per:
                acad_per = f"{year}-{per}"
            elif year:
                acad_per = str(year)
            else:
                acad_per = "2024-B1"

        X.append(features)
        y.append(target)
        groups.append(group)
        metadata.append({
            'student_id': group,
            'academic_year': year,
            'period': per,
            'academic_period': acad_per,
            'cutoff_date': r.get('cutoff_date'),
        })

    X_arr = np.array(X, dtype=float)
    y_arr = np.array(y, dtype=int)
    groups_arr = np.array(groups, dtype=int)

    assert X_arr.shape[1] == len(feature_cols), "La dimensión de X debe coincidir exactamente con el número de features"

    return X_arr, y_arr, groups_arr, feature_cols, metadata


def parse_period_sort_key(period_str: str) -> Tuple[int, int, str]:
    """Genera tupla cronológica para ordenar periodos académicos (ej. '2023-B1' < '2024-B2')."""
    raw = str(period_str).strip()
    year = 0
    part_num = 0

    m_year = re.search(r'(19\d\d|20\d\d)', raw)
    if m_year:
        year = int(m_year.group(1))

    remainder = raw.replace(str(year), '') if year else raw
    m_num = re.search(r'(\d+)', remainder)
    if m_num:
        part_num = int(m_num.group(1))

    return (year, part_num, raw)


def split_dataset(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    metadata: List[Dict[str, Any]],
    split_strategy: str = 'temporal',
    test_period: Optional[str] = None,
    test_size: float = 0.25,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, str, Optional[str]]:
    """Separa observaciones en train y test según estrategia temporal o agrupada."""
    row_periods = [str(m['academic_period']) for m in metadata]
    unique_periods = sorted(list(set(row_periods)), key=parse_period_sort_key)

    if split_strategy == 'temporal':
        if len(unique_periods) < 2 and test_period is None:
            print(f"AVISO: El dataset contiene solo 1 periodo académico ({unique_periods}).")
            print("       No es posible realizar partición temporal inter-periodo.")
            print("       Activando fallback seguro a 'GroupShuffleSplit' por estudiante.")
        else:
            selected_test_period = test_period if test_period else unique_periods[-1]
            if selected_test_period not in row_periods:
                print(f"AVISO: El periodo de prueba solicitado '{selected_test_period}' no existe en el dataset.")
                print(f"       Periodos disponibles: {unique_periods}. Fallback a 'GroupShuffleSplit'.")
            else:
                test_idx = np.array([i for i, p in enumerate(row_periods) if p == selected_test_period], dtype=int)
                test_key = parse_period_sort_key(selected_test_period)
                train_idx = np.array([
                    i for i, p in enumerate(row_periods)
                    if p != selected_test_period and parse_period_sort_key(p) < test_key
                ], dtype=int)

                if len(train_idx) == 0:
                    train_idx = np.array([i for i, p in enumerate(row_periods) if p != selected_test_period], dtype=int)

                unique_y_train = len(set(y[train_idx])) if len(train_idx) > 0 else 0
                unique_y_test = len(set(y[test_idx])) if len(test_idx) > 0 else 0

                if len(train_idx) < 2 or len(test_idx) < 2 or unique_y_train < 2 or unique_y_test < 2:
                    print("AVISO: La partición temporal deja muestras insuficientes o mono-clase en train/test.")
                    print("       Activando fallback a 'GroupShuffleSplit' para garantizar métricas supervisadas válidas.")
                else:
                    return train_idx, test_idx, 'temporal', selected_test_period

    # GroupShuffleSplit por student_id (garantiza que ningún estudiante esté en train y test simultáneamente)
    unique_students = len(set(groups))
    if unique_students < 4:
        raise ValueError(
            f"Se requieren al menos 4 estudiantes diferentes en el dataset para una evaluación confiable (encontrados: {unique_students})."
        )

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    return train_idx, test_idx, 'group', None


def build_candidate_pipelines(feature_cols: List[str]) -> Dict[str, Pipeline]:
    """Define los pipelines candidatos a comparar sin asumir ganador a priori."""
    return {
        'logistic_regression': Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(max_iter=1000, random_state=42)),
        ]),
        'decision_tree': Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('classifier', DecisionTreeClassifier(max_depth=4, min_samples_leaf=3, random_state=42)),
        ]),
        'random_forest': Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('classifier', RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_leaf=2, random_state=42)),
        ]),
    }


def train_and_select_best_model(
    dataset_path: Path,
    output_dir: Path,
    split_strategy: str = 'temporal',
    test_period: Optional[str] = None,
    test_size: float = 0.25,
    random_state: int = 42,
) -> Dict[str, Any]:
    print(f"\n--- Iniciando Pipeline de Entrenamiento Supervisado ---")
    print(f"Cargando dataset desde: {dataset_path}")
    X, y, groups, feature_cols, metadata = load_dataset(dataset_path)

    n_samples, n_features = X.shape
    unique_students = len(set(groups))
    positives = int(np.sum(y == 1))
    negatives = int(np.sum(y == 0))

    print(f"Observaciones: {n_samples} | Características en X: {n_features} | Estudiantes únicos: {unique_students}")
    print(f"Features predictivas activas ({len(feature_cols)}): {feature_cols}")
    print(f"Seguridad: Identificadores excluidos de X (usados solo para partición y agrupamiento).")
    print(f"Balance de clases: Negativo={negatives} ({(negatives/n_samples)*100:.1f}%), Positivo/Riesgo={positives} ({(positives/n_samples)*100:.1f}%)")

    # Separación Train / Test
    train_idx, test_idx, strategy_used, test_period_used = split_dataset(
        X, y, groups, metadata,
        split_strategy=split_strategy,
        test_period=test_period,
        test_size=test_size,
        random_state=random_state,
    )

    print(f"\nEstrategia de Evaluación: {strategy_used.upper()}")
    if strategy_used == 'temporal':
        print(f"  Periodo de Evaluación (Test): {test_period_used} ({len(test_idx)} muestras)")
        train_periods = sorted(list(set(metadata[i]['academic_period'] for i in train_idx)), key=parse_period_sort_key)
        print(f"  Periodos de Entrenamiento (Train): {train_periods} ({len(train_idx)} muestras)")
    else:
        print(f"  GroupShuffleSplit por student_id (Train: {len(train_idx)}, Test: {len(test_idx)}, test_size={test_size})")

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    candidates = build_candidate_pipelines(feature_cols)
    results = {}
    best_name = None
    best_pipeline = None
    best_f1_risk = -1.0

    print("\n--- Comparación de Modelos Candidatos ---")
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        y_proba = None
        if hasattr(pipeline, 'predict_proba'):
            try:
                y_proba = pipeline.predict_proba(X_test)[:, 1]
            except Exception:
                y_proba = None

        metrics = compute_classification_metrics(y_test, y_pred, y_proba)
        results[name] = metrics

        f1_risk = metrics.get('positive_class_f1', 0.0)
        recall_risk = metrics.get('positive_class_recall', 0.0)
        acc = metrics.get('accuracy', 0.0)
        print(f"Modelo: {name:<22} | Acc: {acc:.3f} | Recall Riesgo: {recall_risk:.3f} | F1 Riesgo: {f1_risk:.3f}")

        # Criterio de selección: optimizar F1 de la clase positiva (riesgo)
        if f1_risk > best_f1_risk:
            best_f1_risk = f1_risk
            best_name = name
            best_pipeline = pipeline

    print(f"\nModelo Seleccionado: {best_name} (F1 Riesgo = {best_f1_risk:.3f})")

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dest = output_dir / 'student_risk_pipeline.joblib'
    meta_dest = output_dir / 'metadata.json'

    joblib.dump(best_pipeline, model_dest)
    print(f"Artefacto serializado guardado en: {model_dest}")

    metadata_out = {
        'available': True,
        'status': 'MODEL_AVAILABLE',
        'version': f'v1_{datetime.now().strftime("%Y%m%d")}',
        'selected_algorithm': best_name,
        'split_strategy': strategy_used,
        'temporal_test_period': test_period_used,
        'trained_at': datetime.now().isoformat(),
        'dataset_path': str(dataset_path),
        'features': feature_cols,
        'excluded_identifiers': ['student_id', 'student_code', 'academic_year', 'period', 'cutoff_date'],
        'test_metrics': results[best_name],
        'comparison_results': results,
        'dataset_summary': {
            'total_samples': n_samples,
            'unique_students': unique_students,
            'positive_class_count': positives,
            'negative_class_count': negatives,
        },
    }

    with meta_dest.open('w', encoding='utf-8') as f:
        json.dump(metadata_out, f, indent=2, ensure_ascii=False)
    print(f"Metadatos guardados en: {meta_dest}")

    return metadata_out


def main():
    parser = argparse.ArgumentParser(description="Entrena y compara modelos supervisados para riesgo académico.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "ml" / "datasets" / "processed" / "training_dataset.csv", help="Ruta al CSV procesado.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "ml" / "models", help="Directorio destino de artefactos.")
    parser.add_argument("--split-strategy", choices=["temporal", "group"], default="temporal", help="Estrategia de evaluación (temporal o por grupo de alumnos).")
    parser.add_argument("--test-period", type=str, default=None, help="Periodo académico para conjunto de prueba (ej. '2024-B2').")
    args = parser.parse_args()

    if not args.dataset.is_file():
        print("AVISO: No se encontró el dataset de entrenamiento.")
        print(f"Ruta esperada: {args.dataset}")
        print("Para generar el dataset:")
        print("  1. Importe datos reales: python ml/scripts/import_historical_data.py <archivo.csv>")
        print("  2. Construya la matriz:  python ml/scripts/build_dataset.py --cutoff-date YYYY-MM-DD")
        sys.exit(0)

    try:
        train_and_select_best_model(
            args.dataset,
            args.output_dir,
            split_strategy=args.split_strategy,
            test_period=args.test_period,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
