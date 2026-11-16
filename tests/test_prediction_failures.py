from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from ml.pipeline.predictor import AcademicRiskPredictor
from services.ml.prediction_service import RiskPredictionService
from services.ml_service import build_prediction_payload


FEATURES = {'total_attempts': 2, 'average_score': 12, 'last_score': 11}
METADATA = {'name': 'TestClassifier', 'version': 'test', 'dataset_source': 'benchmark', 'features': list(FEATURES)}


def predictor(probabilities=None, classes=(0, 1), prediction=(1,)):
    model = Mock()
    model.classes_ = np.asarray(classes)
    model.predict_proba.return_value = [[0.2, 0.8]] if probabilities is None else probabilities
    model.predict.return_value = prediction
    return AcademicRiskPredictor(Path('unused'), model=model, metadata=METADATA), model


def test_probability_failure_never_becomes_fifty_percent():
    engine, model = predictor()
    model.predict_proba.side_effect = RuntimeError('internal details must stay private')
    result = engine.predict(FEATURES)
    assert result['success'] is False
    assert result['code'] == 'PREDICTION_ERROR'
    assert result['risk_probability'] is None and result['predicted_class'] is None
    assert result['prediction'] == {'risk_level': 'UNKNOWN', 'probability': None}
    assert 'internal details' not in str(result)
    model.predict.assert_not_called()


@pytest.mark.parametrize('probabilities', [[[float('nan'), 0.5]], [[0.1, float('inf')]],
                                         [[-0.1, 1.1]], [[0.2, 0.2]], [[0.8]], [[0.2, 0.4, 0.4]]])
def test_invalid_probability_output_is_unavailable(probabilities):
    engine, _ = predictor(probabilities)
    result = engine.predict(FEATURES)
    assert result['success'] is False
    assert result['risk_probability'] is None


def test_class_prediction_failure_is_not_replaced_by_a_threshold_rule():
    engine, model = predictor()
    model.predict.side_effect = RuntimeError('failed')
    result = engine.predict(FEATURES)
    assert result['code'] == 'PREDICTION_ERROR'
    assert result['predicted_class'] is None


def test_positive_class_is_found_by_label_and_not_column_position():
    engine, _ = predictor([[0.8, 0.2]], classes=(1, 0))
    result = engine.predict(FEATURES)
    assert result['success'] is True
    assert result['risk_probability'] == 0.8
    assert result['risk_level'] == 'Alto'


@pytest.mark.parametrize('value', ['invalid', float('nan'), float('inf')])
def test_invalid_features_do_not_reach_the_model(value):
    engine, model = predictor()
    result = engine.predict({**FEATURES, 'average_score': value})
    assert result['code'] == 'INVALID_FEATURES'
    model.predict_proba.assert_not_called()


def test_missing_history_is_not_a_risk_classification_or_a_tutoring_alert():
    engine, _ = predictor()
    result = engine.predict({'total_attempts': 0})
    assert result['code'] == 'INSUFFICIENT_HISTORY'
    assert result['risk_probability'] is None and result['predicted_class'] is None
    with patch('services.ml_service.get_risk_prediction_service') as factory:
        factory.return_value.predict_for_student.return_value = result
        payload = build_prediction_payload(student_id=1)
    assert payload['risk_level'] == 'Sin datos'
    assert 'Alerta temprana' not in payload['recommendation']


def test_prediction_error_code_survives_the_teacher_payload_adapter():
    engine, model = predictor()
    model.predict.side_effect = RuntimeError('failed')
    result = engine.predict(FEATURES)
    with patch('services.ml_service.get_risk_prediction_service') as factory:
        factory.return_value.predict_for_student.return_value = result
        payload = build_prediction_payload(student_id=1)
    assert payload['code'] == 'PREDICTION_ERROR'
    assert payload['risk_probability'] is None and payload['level'] == 'No disponible'


def test_database_failure_is_not_reported_as_no_student_history():
    registry = Mock()
    registry.is_available.return_value = True
    registry.base_dir = Path('unused')
    registry.get_metadata.return_value = METADATA
    engine, model = predictor()
    registry.get_model.return_value = model
    service = RiskPredictionService(registry)
    with patch('services.ml.prediction_service.FeatureService.extract_features_for_student', side_effect=RuntimeError('db unavailable')):
        result = service.predict_for_student(1)
    assert result['code'] == 'FEATURE_DATA_UNAVAILABLE'
    assert result['success'] is False and result['risk_probability'] is None
