from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import numpy as np

from services.ml.feature_service import FeatureService
from services.ml.model_registry import ModelRegistry, get_model_registry
from ml.pipeline.predictor import AcademicRiskPredictor


class RiskPredictionService:
    """Servicio de inferencia en producción para estimación y explicación de riesgo académico."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()
        self._pipeline_predictor: Optional[AcademicRiskPredictor] = None

    def _get_predictor(self) -> AcademicRiskPredictor:
        cached_model = self.registry.get_model()
        meta = self.registry.get_metadata()
        if (
            self._pipeline_predictor is None
            or self._pipeline_predictor.model_dir != self.registry.base_dir
            or getattr(self._pipeline_predictor, '_model', None) != cached_model
        ):
            self._pipeline_predictor = AcademicRiskPredictor(
                self.registry.base_dir,
                model=cached_model,
                metadata=meta,
            )
        return self._pipeline_predictor

    def is_available(self) -> bool:
        return self.registry.is_available()

    def get_status(self) -> Dict[str, Any]:
        return self.registry.get_metadata()

    def predict_for_features(self, feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza inferencia sobre un diccionario de características con motor de explicabilidad."""
        if not self.is_available():
            meta = self.registry.get_metadata()
            return {
                'success': False,
                'code': 'MODEL_NOT_AVAILABLE',
                'status': 'MODEL_NOT_AVAILABLE',
                'message': meta.get('message') or 'El modelo de riesgo académico todavía no ha sido entrenado.',
                'risk_level': 'No disponible',
                'risk_probability': None,
                'predicted_class': None,
                'prediction': {'risk_level': 'UNKNOWN', 'probability': None},
                'model': {'name': 'None', 'version': None, 'dataset': self.registry.source},
                'main_factors': ['Modelo no disponible'],
                'explanation': ['model not available'],
            }

        predictor = self._get_predictor()
        res = predictor.predict(feature_dict)
        if not res.get('success'):
            return res

        metadata = self.registry.get_metadata()
        risk_prob = res.get('risk_probability')
        risk_level = res.get('risk_level', 'Bajo')

        return {
            'success': True,
            'risk_probability': risk_prob,
            'predicted_class': res.get('predicted_class', 0),
            'risk_level': risk_level,
            'prediction': res.get('prediction', {'risk_level': 'LOW', 'probability': risk_prob}),
            'model': res.get('model', {'name': metadata.get('name', 'SupervisedModel'), 'version': metadata.get('version', 'v1'), 'dataset': self.registry.source}),
            'model_version': metadata.get('version', 'v1'),
            'main_factors': res.get('main_factors', []),
            'explanation': res.get('explanation', []),
            'features_used': res.get('features_used', {}),
        }

    def predict_for_student(
        self,
        student_id: int,
        cutoff_date: Union[str, None] = None,
    ) -> Dict[str, Any]:
        """Extrae características del estudiante antes del cutoff y ejecuta inferencia explicable."""
        if not self.is_available():
            meta = self.registry.get_metadata()
            return {
                'success': False,
                'code': 'MODEL_NOT_AVAILABLE',
                'status': 'MODEL_NOT_AVAILABLE',
                'message': meta.get('message') or 'El modelo de riesgo académico todavía no ha sido entrenado.',
                'student_id': int(student_id),
                'risk_level': 'No disponible',
                'risk_probability': None,
                'predicted_class': None,
                'cutoff_date': cutoff_date,
                'prediction': {'risk_level': 'UNKNOWN', 'probability': None},
                'model': {'name': 'None', 'version': None, 'dataset': self.registry.source},
                'main_factors': ['Modelo no disponible'],
                'explanation': ['model not available'],
            }

        features = FeatureService.extract_features_for_student(
            student_id=student_id,
            cutoff_date=cutoff_date,
        )

        result = self.predict_for_features(features)
        result['student_id'] = int(student_id)
        result['cutoff_date'] = cutoff_date
        return result

    def predict_for_students_batch(
        self,
        students: List[Dict[str, Any]],
        cutoff_date: Union[str, None] = None,
    ) -> List[Dict[str, Any]]:
        """Realiza predicciones por lote para una lista de estudiantes."""
        results = []
        for s in students or []:
            sid = s.get('id') or s.get('student_id')
            if sid is None:
                continue
            pred = self.predict_for_student(int(sid), cutoff_date=cutoff_date)
            results.append({
                'student_id': int(sid),
                'student_name': f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or f'Estudiante {sid}',
                'grade': s.get('grade'),
                **pred,
            })
        return results


_PREDICTION_SERVICE_INSTANCE: Optional[RiskPredictionService] = None


def get_risk_prediction_service() -> RiskPredictionService:
    global _PREDICTION_SERVICE_INSTANCE
    if _PREDICTION_SERVICE_INSTANCE is None:
        _PREDICTION_SERVICE_INSTANCE = RiskPredictionService()
    return _PREDICTION_SERVICE_INSTANCE
