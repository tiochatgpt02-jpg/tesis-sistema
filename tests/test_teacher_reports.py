import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.ml_service import build_prediction_payload
from services.teacher_reports_service import build_report_summary, build_student_risk_analysis


def test_build_prediction_payload_returns_model_not_available_when_untrained():
    from unittest.mock import patch
    from services.ml.model_registry import get_model_registry

    registry = get_model_registry()
    with patch.object(registry, 'is_available', return_value=False):
        payload = build_prediction_payload('Ana', 17, 'actividades',student_id=999)
        assert payload['success'] is False
        assert payload['code'] == 'MODEL_NOT_AVAILABLE'
        assert 'no ha sido entrenado' in payload['message'].lower()


def test_build_prediction_payload_with_real_trained_model_on_disk():
    # Tests real prediction when trained model is available
    from services import db_service
    db_service.record_student_result(1,score=12)
    db_service.record_student_result(1,score=16)
    payload = build_prediction_payload('Carlos', 16.5, 'actividades',student_id=1)
    assert payload['success'] is True
    assert payload['risk_level'] in {'Bajo', 'Medio', 'Alto'}
    assert payload['level'] in {'excelente', 'bueno', 'necesita apoyo'}
    assert payload['risk_probability'] is not None
    assert payload['student_id']==1
    assert payload['validation_scope']=='benchmark'
    assert 'no constituyen una validación' in payload['notice']


def test_build_prediction_payload_with_trained_model():
    from unittest.mock import MagicMock
    from services.ml.model_registry import get_model_registry

    registry = get_model_registry()
    dummy_model = MagicMock()
    dummy_model.classes_ = [0, 1]
    dummy_model.predict.return_value = [0]
    dummy_model.predict_proba.return_value = [[0.85, 0.15]]

    orig_model = registry._cached_model
    orig_meta = registry._cached_metadata
    try:
        registry._cached_model = dummy_model
        registry._cached_metadata = {'status': 'AVAILABLE', 'version': 'v1_test', 'features': registry.DEFAULT_FEATURE_NAMES}
        payload = build_prediction_payload('Computación', 18, 'actividades',student_id=1)
        assert payload['success'] is True
        assert payload['risk_level'] in {'Bajo', 'Medio', 'Alto'}
        assert payload['level'] in {'excelente', 'bueno', 'necesita apoyo'}
        assert payload['risk_probability']==0.15
        assert payload['recommendation']=='Mantener el plan de trabajo actual y proponer desafíos complementarios.'
    finally:
        registry._cached_model = orig_model
        registry._cached_metadata = orig_meta


def test_build_report_summary_includes_grade_totals():
    summary = build_report_summary(
        students=[
            {'grade': 4, 'progress': 60},
            {'grade': 5, 'progress': 70},
            {'grade': 5, 'progress': 80},
        ],
        topics=[{'title': 'Word'}, {'title': 'Excel'}],
    )
    assert summary['total_students'] == 3
    assert summary['total_topics'] == 2
    assert '5' in summary['report_by_grade']


def test_build_student_risk_analysis_does_not_invent_risk_from_progress():
    risk = build_student_risk_analysis({'first_name': 'Ana', 'last_name': 'Martínez', 'progress': 40})
    assert risk['risk_level'] == 'no disponible'
    assert risk['risk_probability'] is None
    assert risk['method'] == 'unavailable'
    assert risk['ml_status'] == 'STUDENT_REQUIRED'
