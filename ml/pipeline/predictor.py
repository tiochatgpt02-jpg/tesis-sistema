"""Inferencia y motor de explicabilidad para predicción temprana de riesgo escolar.

Traduce las salidas numéricas del modelo supervisado y la importancia relativa de variables
en factores pedagógicos explicables en lenguaje natural comprensible para el docente.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np

from ml.pipeline.feature_builder import CANONICAL_FEATURES


class AcademicRiskPredictor:
    """Clase principal de inferencia y explicabilidad para el sistema escolar."""

    def __init__(
        self,
        model_dir: Path,
        model: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / 'model.joblib'
        self.metadata_path = self.model_dir / 'metadata.json'
        self.features_json_path = self.model_dir / 'features.json'

        self._model = model
        self._metadata = metadata
        self._features = None

    def is_available(self) -> bool:
        """Verifica si el modelo serializado está disponible en memoria o en disco."""
        if self._model is not None:
            return True
        return self.model_path.is_file() and self.metadata_path.is_file()

    def get_metadata(self) -> Dict[str, Any]:
        """Carga y cachea la metadata del modelo."""
        if self._metadata is not None:
            return self._metadata

        if self.metadata_path.is_file():
            try:
                with self.metadata_path.open('r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                    return self._metadata
            except Exception:
                pass

        return {
            'available': False,
            'status': 'MODEL_NOT_AVAILABLE',
            'version': None,
            'name': 'None',
            'dataset_source': 'unknown',
            'message': 'Modelo no disponible.',
        }

    def get_features(self) -> List[str]:
        """Retorna la lista ordenada de variables predictivas."""
        if self._features is not None:
            return self._features

        meta = self.get_metadata()
        feats = meta.get('features')
        if feats:
            self._features = feats
            return feats

        if self.features_json_path.is_file():
            try:
                with self.features_json_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._features = data.get('canonical_features', CANONICAL_FEATURES)
                    return self._features
            except Exception:
                pass

        self._features = CANONICAL_FEATURES
        return self._features

    def get_model(self) -> Optional[Any]:
        """Carga en memoria el artefacto joblib."""
        if self._model is not None:
            return self._model
        if not self.is_available():
            return None
        try:
            self._model = joblib.load(self.model_path)
            return self._model
        except Exception:
            return None

    def explain_prediction(
        self,
        features_dict: Dict[str, Any],
        risk_probability: float,
        predicted_class: int,
    ) -> Tuple[List[str], List[str]]:
        """Genera explicaciones pedagógicas en español y descriptores técnicos en inglés.
        
        Retorna:
          Tuple[main_factors_es, explanation_en]
        """
        main_factors: List[str] = []
        explanation: List[str] = []

        total_attempts = float(features_dict.get('total_attempts', 0) or 0)
        avg_score = float(features_dict.get('average_score', 0) or 0)
        avg_eval = float(features_dict.get('average_evaluation_score', 0) or 0)
        eval_count = float(features_dict.get('evaluation_count', 0) or 0)
        act_count = float(features_dict.get('activities_count', 0) or 0)
        trend = float(features_dict.get('score_trend', 0) or 0)
        last_score = float(features_dict.get('last_score', 0) or 0)
        accuracy = float(features_dict.get('accuracy_ratio', 0) or 0)
        correct = float(features_dict.get('total_correct_answers', 0) or 0)
        wrong = float(features_dict.get('total_wrong_answers', 0) or 0)

        # Si no hay historial
        if total_attempts == 0:
            return (
                ["Sin actividades ni evaluaciones registradas para el estudiante"],
                ["no historical activity or assessment records"]
            )

        # Si presenta riesgo medio o alto
        if risk_probability >= 0.35 or predicted_class == 1:
            if avg_eval > 0 and avg_eval < 11.0:
                main_factors.append("Bajo rendimiento en evaluaciones formativas (promedio menor a 11)")
                explanation.append("low evaluation performance")
            elif avg_score < 11.0:
                main_factors.append("Promedio general de notas por debajo del umbral aprobatorio")
                explanation.append("average score below passing threshold")

            if trend < -0.8:
                main_factors.append("Últimas notas muestran tendencia fuertemente negativa")
                explanation.append("average_score decreased significantly")
            elif trend < -0.2:
                main_factors.append("Tendencia descendente en las últimas calificaciones")
                explanation.append("recent grades downward trend")

            if last_score > 0 and last_score < 11.0:
                main_factors.append(f"Última calificación registrada en nivel reprobatorio ({last_score:.1f}/20)")
                explanation.append("last recorded score in failing range")

            if act_count < 2 and total_attempts <= 3:
                main_factors.append("Pocas actividades formativas completadas")
                explanation.append("few activities completed")

            if (correct + wrong) > 5 and accuracy < 0.55:
                main_factors.append("Alta proporción de respuestas incorrectas en actividades de aula")
                explanation.append("high error rate in classroom activities")

            if not main_factors:
                main_factors.append("Desempeño general cercano al límite de aprobación")
                explanation.append("overall performance close to risk threshold")

        else:
            # Estudiante en bajo riesgo
            if avg_score >= 14.0:
                main_factors.append("Desempeño destacado con promedio aprobatorio consolidado")
                explanation.append("strong continuous performance")
            else:
                main_factors.append("Rendimiento regular dentro de los rangos de aprobación")
                explanation.append("steady passing performance")

            if trend > 0.5:
                main_factors.append("Tendencia de mejora en las evaluaciones recientes")
                explanation.append("recent positive grade trend")

            if act_count >= 2:
                main_factors.append("Participación constante en actividades del periodo")
                explanation.append("consistent activity participation")

        return main_factors[:3], explanation[:3]

    def predict(self, feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza inferencia completa y genera respuesta estructurada."""
        if not self.is_available():
            return {
                'success': False,
                'code': 'MODEL_NOT_AVAILABLE',
                'status': 'MODEL_NOT_AVAILABLE',
                'message': 'El modelo predictivo no está disponible. Requiere entrenamiento previo.',
                'prediction': {
                    'risk_level': 'UNKNOWN',
                    'probability': None,
                },
                'model': {
                    'name': 'None',
                    'version': None,
                    'dataset': self.model_dir.name,
                },
                'main_factors': ['Modelo no entrenado'],
                'explanation': ['model not available'],
            }

        model = self.get_model()
        if model is None:
            return {
                'success': False,
                'code': 'MODEL_LOAD_ERROR',
                'message': 'No fue posible cargar el modelo desde disco.',
                'prediction': {'risk_level': 'ERROR', 'probability': None},
                'model': {'name': 'None', 'version': None, 'dataset': self.model_dir.name},
                'main_factors': ['Error de carga del modelo'],
                'explanation': ['model load error'],
            }

        try:
            total_attempts = float(feature_dict.get('total_attempts', 0) or 0)
            feature_names = self.get_features()
            vector = [float(feature_dict.get(key, 0.0) or 0.0) for key in feature_names]
            X = np.array([vector], dtype=float)
            if not np.isfinite(X).all() or not np.isfinite(total_attempts):
                raise ValueError('Non-finite input')
        except (TypeError, ValueError, OverflowError):
            return self._unavailable_prediction('INVALID_FEATURES', 'Los datos académicos no permiten calcular una predicción válida.')
        # Si un alumno no tiene historial absoluto
        if total_attempts == 0 and not any(feature_dict.get(k) for k in ['average_score', 'last_score']):
            return {
                'success': True,
                'code': 'INSUFFICIENT_HISTORY',
                'status': 'INSUFFICIENT_HISTORY',
                'predicted_class': None,
                'prediction': {
                    'risk_level': 'UNKNOWN',
                    'probability': None,
                },
                'model': {
                    'name': self.get_metadata().get('name', 'SupervisedModel'),
                    'version': self.get_metadata().get('version', '1.0'),
                    'dataset': self.get_metadata().get('dataset_source', self.model_dir.name),
                },
                'main_factors': ['Sin historial previo de notas o actividades registradas para este estudiante'],
                'explanation': ['no student records found'],
                'risk_probability': None,
                'risk_level': 'Sin datos',
            }

        try:
            # The trained binary target is 0=not at risk and 1=at risk.
            # Locate class 1 explicitly instead of assuming its probability column.
            classes = np.asarray(model.classes_)
            if classes.shape != (2,) or set(classes.tolist()) != {0, 1}:
                raise ValueError('Unexpected target labels')
            probabilities = np.asarray(model.predict_proba(X), dtype=float)
            if (probabilities.shape != (1, 2) or not np.isfinite(probabilities).all()
                    or (probabilities < 0).any() or (probabilities > 1).any()
                    or not np.isclose(probabilities[0].sum(), 1.0, atol=1e-6)):
                raise ValueError('Invalid probabilities')
            preds = np.asarray(model.predict(X))
            if preds.shape != (1,) or preds[0] not in (0, 1):
                raise ValueError('Invalid predicted class')
            risk_prob = round(float(probabilities[0, classes.tolist().index(1)]), 4)
            predicted_class = int(preds[0])
        except Exception:
            return self._unavailable_prediction('PREDICTION_ERROR', 'No se pudo calcular la predicción. No se ha asignado un nivel de riesgo.')

        if risk_prob >= 0.65:
            risk_level_code = 'HIGH'
            risk_level_es = 'Alto'
        elif risk_prob >= 0.35:
            risk_level_code = 'MEDIUM'
            risk_level_es = 'Medio'
        else:
            risk_level_code = 'LOW'
            risk_level_es = 'Bajo'

        main_factors_es, explanation_en = self.explain_prediction(
            features_dict=feature_dict,
            risk_probability=risk_prob,
            predicted_class=predicted_class,
        )

        meta = self.get_metadata()
        return {
            'success': True,
            'prediction': {
                'risk_level': risk_level_code,
                'probability': risk_prob,
            },
            'model': {
                'name': meta.get('name', 'SupervisedClassifier'),
                'version': meta.get('version', '1.0'),
                'dataset': meta.get('dataset_source', self.model_dir.name),
            },
            'risk_level': risk_level_es,
            'risk_probability': risk_prob,
            'predicted_class': predicted_class,
            'main_factors': main_factors_es,
            'explanation': explanation_en,
            'features_used': {k: feature_dict.get(k) for k in feature_names},
        }

    def _unavailable_prediction(self, code: str, message: str) -> Dict[str, Any]:
        meta = self.get_metadata()
        return {
            'success': False, 'code': code, 'status': code, 'message': message,
            'risk_probability': None, 'predicted_class': None, 'risk_level': 'No disponible',
            'prediction': {'risk_level': 'UNKNOWN', 'probability': None},
            'model': {'name': meta.get('name'), 'version': meta.get('version'),
                      'dataset': meta.get('dataset_source', self.model_dir.name)},
            'main_factors': ['Predicción no disponible'], 'explanation': [code.lower()],
        }
