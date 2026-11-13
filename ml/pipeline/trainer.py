"""Entrenamiento, comparación multialgorítmica y selección objetiva de modelos supervisados.

Compara:
  - Logistic Regression
  - Decision Tree
  - Random Forest
  - Gradient Boosting

Selección automática con prioridad:
  1. Recall de clase de riesgo (Sensibilidad para detección temprana)
  2. F1-Score de clase de riesgo
  3. ROC-AUC
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

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.pipeline.data_loader import load_training_matrix
from ml.pipeline.preprocessing import create_classification_pipeline
from ml.pipeline.evaluator import compute_classification_metrics, extract_feature_importances


def parse_period_sort_key(period_str: str) -> Tuple[int, int, str]:
    """Ordena cronológicamente periodos del tipo '2023-B1' < '2024-B1'."""
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


def partition_data(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    metadata: List[Dict[str, Any]],
    split_strategy: str = 'temporal',
    test_period: Optional[str] = None,
    test_size: float = 0.25,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Aplica la partición según estrategia temporal o por grupo (GroupShuffleSplit)."""
    row_periods = [str(m.get('academic_period') or '') for m in metadata]
    unique_periods = sorted(list(set(row_periods)), key=parse_period_sort_key)

    val_meta: Dict[str, Any] = {
        'strategy': split_strategy,
        'random_state': random_state,
    }

    if split_strategy == 'temporal' and len(unique_periods) >= 2:
        selected_test = test_period if (test_period and test_period in unique_periods) else unique_periods[-1]
        test_key = parse_period_sort_key(selected_test)

        test_idx = np.array([i for i, p in enumerate(row_periods) if p == selected_test], dtype=int)
        train_idx = np.array([i for i, p in enumerate(row_periods) if p != selected_test and parse_period_sort_key(p) < test_key], dtype=int)

        if len(train_idx) == 0:
            train_idx = np.array([i for i, p in enumerate(row_periods) if p != selected_test], dtype=int)

        y_train_classes = len(set(y[train_idx])) if len(train_idx) > 0 else 0
        y_test_classes = len(set(y[test_idx])) if len(test_idx) > 0 else 0

        if len(train_idx) >= 4 and len(test_idx) >= 4 and y_train_classes >= 2 and y_test_classes >= 2:
            val_meta.update({
                'strategy': 'temporal',
                'train_period': sorted(list(set(row_periods[i] for i in train_idx))),
                'test_period': selected_test,
                'train_samples': len(train_idx),
                'test_samples': len(test_idx),
            })
            return train_idx, test_idx, val_meta

    # Fallback o selección explícita de GroupShuffleSplit por estudiante
    unique_students = len(set(groups))
    if unique_students < 4:
        raise ValueError(f"Se requieren al menos 4 estudiantes diferentes para evaluación (encontrados: {unique_students}).")

    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    val_meta.update({
        'strategy': 'group_split',
        'group_column': 'student_code',
        'train_samples': len(train_idx),
        'test_samples': len(test_idx),
        'unique_students': unique_students,
    })
    return train_idx, test_idx, val_meta


def build_candidate_classifiers() -> Dict[str, Any]:
    """Instancia las 4 familias de algoritmos supervisados para comparación."""
    return {
        'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
        'DecisionTree': DecisionTreeClassifier(max_depth=5, min_samples_split=10, random_state=42),
        'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_split=6, random_state=42),
        'GradientBoosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42),
    }


def train_candidate_models(
    dataset_path: Path,
    output_model_dir: Path,
    split_strategy: str = 'temporal',
    test_period: Optional[str] = None,
    dataset_name: str = 'benchmark',
) -> Dict[str, Any]:
    """Pipeline completo de entrenamiento, evaluación, selección y guardado."""
    X, y, groups, feature_names, metadata = load_training_matrix(dataset_path)

    train_idx, test_idx, val_meta = partition_data(
        X, y, groups, metadata, split_strategy=split_strategy, test_period=test_period
    )

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    classifiers = build_candidate_classifiers()
    results_list: List[Dict[str, Any]] = []
    trained_pipelines: Dict[str, Any] = {}
    model_metrics: Dict[str, Dict[str, Any]] = {}

    for name, clf in classifiers.items():
        pipe = create_classification_pipeline(clf, numeric_features=feature_names)
        pipe.fit(X_train, y_train)
        trained_pipelines[name] = pipe

        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, 'predict_proba') else None

        metrics = compute_classification_metrics(y_test, y_pred, y_proba)
        model_metrics[name] = metrics

        results_list.append({
            'name': name,
            'accuracy': metrics['accuracy'],
            'precision': metrics['positive_class_precision'],
            'recall': metrics['positive_class_recall'],
            'f1': metrics['positive_class_f1'],
            'roc_auc': metrics['roc_auc'] or 0.0,
        })

    # Ordenar según criterios objetivos de negocio:
    # 1. Recall (detección precoz de riesgo)
    # 2. F1-Score
    # 3. ROC-AUC
    results_list.sort(
        key=lambda m: (m['recall'], m['f1'], m['roc_auc'], m['accuracy']),
        reverse=True,
    )
    best_candidate_name = results_list[0]['name']
    best_pipeline = trained_pipelines[best_candidate_name]
    best_metrics = model_metrics[best_candidate_name]

    # Extraer importancia de características
    importances = extract_feature_importances(best_pipeline, feature_names)

    output_model_dir.mkdir(parents=True, exist_ok=True)

    # 1. Guardar model.joblib
    model_dest = output_model_dir / 'model.joblib'
    joblib.dump(best_pipeline, model_dest)

    # 2. Guardar training_results.json
    results_dest = output_model_dir / 'training_results.json'
    with results_dest.open('w', encoding='utf-8') as f:
        json.dump({'models': results_list}, f, indent=2)

    # 3. Guardar validation_metadata.json
    val_dest = output_model_dir / 'validation_metadata.json'
    with val_dest.open('w', encoding='utf-8') as f:
        json.dump(val_meta, f, indent=2, ensure_ascii=False)

    # 4. Guardar metadata.json oficial del modelo
    metadata_payload = {
        'available': True,
        'status': 'MODEL_AVAILABLE',
        'version': f"v1_{datetime.now().strftime('%Y%m%d')}",
        'name': best_candidate_name,
        'selected_algorithm': best_candidate_name,
        'dataset_source': dataset_name,
        'split_strategy': val_meta.get('strategy'),
        'validation_info': val_meta,
        'trained_at': datetime.now().isoformat(),
        'dataset_path': str(dataset_path),
        'features': feature_names,
        'feature_importances': importances,
        'test_metrics': best_metrics,
        'comparison_results': results_list,
        'total_samples': len(y),
        'train_samples': len(train_idx),
        'test_samples': len(test_idx),
    }
    meta_dest = output_model_dir / 'metadata.json'
    with meta_dest.open('w', encoding='utf-8') as f:
        json.dump(metadata_payload, f, indent=2, ensure_ascii=False)

    print(f"\n--- Comparación Multimodelo Completada ({dataset_name}) ---")
    for r in results_list:
        print(f"Modelo: {r['name']:<18} | Acc: {r['accuracy']:.4f} | Recall: {r['recall']:.4f} | F1: {r['f1']:.4f} | ROC-AUC: {r['roc_auc']:.4f}")
    print(f"\nModelo Ganador Seleccionado: {best_candidate_name} (Recall: {best_metrics['positive_class_recall']:.4f})")
    print(f"Artefactos guardados en: {output_model_dir}")

    return metadata_payload


def main():
    parser = argparse.ArgumentParser(description="Entrena y compara modelos supervisados para riesgo escolar.")
    parser.add_argument("--source", choices=["benchmark", "institutional"], default="benchmark", help="Fuente del dataset.")
    parser.add_argument("--dataset", type=Path, default=None, help="Ruta directa al archivo CSV procesado.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directorio de artefactos destino.")
    parser.add_argument("--split-strategy", choices=["temporal", "group"], default="temporal", help="Estrategia de partición.")
    parser.add_argument("--test-period", type=str, default=None, help="Periodo académico para conjunto de test.")
    args = parser.parse_args()

    dataset_path = args.dataset or (ROOT / "ml" / "datasets" / args.source / "processed" / "training_dataset.csv")
    output_dir = args.output_dir or (ROOT / "ml" / "models" / args.source)

    if not dataset_path.is_file():
        # Fallback a ubicación procesada previa
        legacy_path = ROOT / "ml" / "datasets" / "processed" / "training_dataset.csv"
        if legacy_path.is_file():
            dataset_path = legacy_path
        else:
            print(f"ERROR: No se encontró el dataset en {dataset_path}", file=sys.stderr)
            sys.exit(1)

    train_candidate_models(
        dataset_path=dataset_path,
        output_model_dir=output_dir,
        split_strategy=args.split_strategy,
        test_period=args.test_period,
        dataset_name=args.source,
    )


if __name__ == '__main__':
    main()
