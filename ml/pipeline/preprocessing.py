"""Definición y construcción de transformadores de preprocesamiento dentro de scikit-learn.

Garantía Metodológica:
  Todo el preprocesamiento (imputación, escalado, codificación) se realiza
  estrictamente dentro de objetos `Pipeline` o `ColumnTransformer` de scikit-learn.
  Bajo ninguna circunstancia se realizan transformaciones manuales fuera del pipeline,
  evitando fuga de información (data leakage) entre particiones de entrenamiento y prueba.
"""

from __future__ import annotations

from typing import Any, List, Optional
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder


def create_preprocessor(
    numeric_features: List[str],
    categorical_features: Optional[List[str]] = None,
    imputer_strategy: str = 'median',
):
    """Crea un preprocesador de scikit-learn con aislamiento completo."""
    if not categorical_features:
        return Pipeline([
            ('imputer', SimpleImputer(strategy=imputer_strategy)),
            ('scaler', StandardScaler()),
        ])

    num_indices = list(range(len(numeric_features)))
    cat_indices = list(range(len(numeric_features), len(numeric_features) + len(categorical_features)))

    numeric_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy=imputer_strategy)),
        ('scaler', StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ('numeric', numeric_pipe, num_indices),
            ('categorical', cat_pipe, cat_indices),
        ],
        remainder='drop',
    )


def create_classification_pipeline(
    classifier: BaseEstimator,
    numeric_features: List[str],
    categorical_features: Optional[List[str]] = None,
    imputer_strategy: str = 'median',
) -> Pipeline:
    """Ensambla el preprocesador y el estimador supervisado en un único Pipeline reproducible."""
    preprocessor = create_preprocessor(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        imputer_strategy=imputer_strategy,
    )

    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', classifier),
    ])
