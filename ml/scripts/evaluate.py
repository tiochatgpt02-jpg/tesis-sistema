from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Calcula métricas de evaluación destacando el rendimiento en la clase de riesgo (positiva)."""
    y_t = np.array(y_true, dtype=int)
    y_p = np.array(y_pred, dtype=int)

    acc = float(accuracy_score(y_t, y_p))

    # Métricas específicas de la clase positiva (riesgo = 1)
    prec_pos = float(precision_score(y_t, y_p, pos_label=1, zero_division=0))
    rec_pos = float(recall_score(y_t, y_p, pos_label=1, zero_division=0))
    f1_pos = float(f1_score(y_t, y_p, pos_label=1, zero_division=0))

    # Métricas macro
    prec_macro = float(precision_score(y_t, y_p, average='macro', zero_division=0))
    rec_macro = float(recall_score(y_t, y_p, average='macro', zero_division=0))
    f1_macro = float(f1_score(y_t, y_p, average='macro', zero_division=0))

    cm = confusion_matrix(y_t, y_p).tolist()

    # ROC-AUC si hay probabilidades y al menos dos clases presentes
    roc_auc: Optional[float] = None
    if y_proba is not None and len(set(y_t)) > 1:
        try:
            roc_auc = round(float(roc_auc_score(y_t, y_proba)), 4)
        except Exception:
            roc_auc = None

    report = classification_report(y_t, y_p, output_dict=True, zero_division=0)

    return {
        'accuracy': round(acc, 4),
        'positive_class_precision': round(prec_pos, 4),
        'positive_class_recall': round(rec_pos, 4),
        'positive_class_f1': round(f1_pos, 4),
        'macro_precision': round(prec_macro, 4),
        'macro_recall': round(rec_macro, 4),
        'macro_f1': round(f1_macro, 4),
        'confusion_matrix': cm,
        'roc_auc': roc_auc,
        'classification_report': report,
    }


def main():
    import argparse
    from pathlib import Path
    import joblib

    parser = argparse.ArgumentParser(description="Evalúa un modelo serializado en un dataset de prueba.")
    parser.add_argument("--model", type=Path, required=True, help="Ruta al archivo .joblib del modelo.")
    parser.add_argument("--test-data", type=Path, required=True, help="Ruta al CSV con X e y.")
    args = parser.parse_args()

    # Carga y evaluación
    from ml.scripts.train import load_dataset

    pipeline = joblib.load(args.model)
    X, y, _, _, _ = load_dataset(args.test_data)
    y_pred = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1] if hasattr(pipeline, 'predict_proba') else None

    metrics = compute_classification_metrics(y, y_pred, y_proba)
    print("\n--- Resultados de Evaluación ---")
    print(f"Accuracy:         {metrics['accuracy']:.4f}")
    print(f"Recall (Riesgo):  {metrics['positive_class_recall']:.4f}")
    print(f"Precision (Riesgo): {metrics['positive_class_precision']:.4f}")
    print(f"F1 (Riesgo):      {metrics['positive_class_f1']:.4f}")
    if metrics['roc_auc'] is not None:
        print(f"ROC-AUC:          {metrics['roc_auc']:.4f}")
    print(f"Matriz de confusión:\n{np.array(metrics['confusion_matrix'])}")


if __name__ == '__main__':
    main()
