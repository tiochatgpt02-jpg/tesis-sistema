"""Módulo de evaluación rigurosa y extracción de importancia de características."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
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
    """Calcula métricas globales y focalizadas en la clase de riesgo académico (positiva, 1)."""
    y_t = np.array(y_true, dtype=int)
    y_p = np.array(y_pred, dtype=int)

    acc = float(accuracy_score(y_t, y_p))

    # Métricas de la clase positiva (Riesgo = 1)
    prec_pos = float(precision_score(y_t, y_p, pos_label=1, zero_division=0))
    rec_pos = float(recall_score(y_t, y_p, pos_label=1, zero_division=0))
    f1_pos = float(f1_score(y_t, y_p, pos_label=1, zero_division=0))

    # Métricas macro
    prec_macro = float(precision_score(y_t, y_p, average='macro', zero_division=0))
    rec_macro = float(recall_score(y_t, y_p, average='macro', zero_division=0))
    f1_macro = float(f1_score(y_t, y_p, average='macro', zero_division=0))

    cm = confusion_matrix(y_t, y_p).tolist()

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


def extract_feature_importances(pipeline_or_classifier: Any, feature_names: List[str]) -> Dict[str, float]:
    """Extrae las contribuciones relativas normalizadas de cada característica predictiva."""
    clf = pipeline_or_classifier
    if hasattr(clf, 'named_steps') and 'classifier' in clf.named_steps:
        clf = clf.named_steps['classifier']

    importances: Dict[str, float] = {}

    # Modelos basados en árboles (Random Forest, Decision Tree, Gradient Boosting)
    if hasattr(clf, 'feature_importances_'):
        raw = clf.feature_importances_
        total = float(np.sum(raw)) if np.sum(raw) > 0 else 1.0
        for name, val in zip(feature_names, raw):
            importances[name] = round(float(val) / total, 4)

    # Modelos lineales (Logistic Regression)
    elif hasattr(clf, 'coef_'):
        coefs = np.abs(clf.coef_[0])
        total = float(np.sum(coefs)) if np.sum(coefs) > 0 else 1.0
        for name, val in zip(feature_names, coefs):
            importances[name] = round(float(val) / total, 4)

    else:
        # Ponderación uniforme por defecto
        w = round(1.0 / len(feature_names), 4) if feature_names else 0.0
        for name in feature_names:
            importances[name] = w

    return importances
