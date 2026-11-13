"""Pipeline modular de Machine Learning para predicción de riesgo académico escolar."""

from __future__ import annotations

from ml.pipeline.data_loader import load_raw_csv, load_training_matrix
from ml.pipeline.preprocessing import create_classification_pipeline, create_preprocessor
from ml.pipeline.feature_builder import CANONICAL_FEATURES, build_processed_matrix, extract_features_from_records
from ml.pipeline.trainer import train_candidate_models
from ml.pipeline.evaluator import compute_classification_metrics, extract_feature_importances
from ml.pipeline.predictor import AcademicRiskPredictor

__all__ = [
    'load_raw_csv',
    'load_training_matrix',
    'create_preprocessor',
    'create_classification_pipeline',
    'CANONICAL_FEATURES',
    'build_processed_matrix',
    'extract_features_from_records',
    'train_candidate_models',
    'compute_classification_metrics',
    'extract_feature_importances',
    'AcademicRiskPredictor',
]
