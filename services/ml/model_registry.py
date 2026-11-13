from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib

from config import Config


class ModelRegistry:
    """Registro y cargador en memoria (Singleton/Cache) de modelos serializados.
    
    Soporta selección de fuente: 'benchmark' vs 'institutional' mediante Config.ML_DATASET_SOURCE.
    """

    DEFAULT_FEATURE_NAMES: List[str] = [
        'total_attempts',
        'evaluation_count',
        'activities_count',
        'games_count',
        'average_score',
        'average_evaluation_score',
        'average_activity_score',
        'min_score',
        'max_score',
        'last_score',
        'score_std',
        'score_trend',
        'total_correct_answers',
        'total_wrong_answers',
        'accuracy_ratio',
        'average_time_spent_seconds',
        'materials_reviewed_count',
        'submissions_count',
    ]

    def __init__(self, base_dir: Optional[Path] = None, source: Optional[str] = None):
        self.source = (source or getattr(Config, 'ML_DATASET_SOURCE', 'benchmark')).strip().lower()
        root_models = Path(__file__).resolve().parents[2] / 'ml' / 'models'

        if base_dir is None:
            self.base_dir = root_models / self.source
        else:
            self.base_dir = Path(base_dir)

        # Buscar model.joblib prioritario en subcarpeta o fallback legado
        primary_model = self.base_dir / 'model.joblib'
        fallback_model = self.base_dir / 'student_risk_pipeline.joblib'
        root_fallback = root_models / 'student_risk_pipeline.joblib'

        if primary_model.is_file():
            self.model_path = primary_model
        elif fallback_model.is_file():
            self.model_path = fallback_model
        elif self.source == 'benchmark' and root_fallback.is_file():
            self.model_path = root_fallback
        else:
            self.model_path = primary_model

        primary_meta = self.base_dir / 'metadata.json'
        root_meta = root_models / 'metadata.json'
        if primary_meta.is_file():
            self.metadata_path = primary_meta
        elif self.source == 'benchmark' and root_meta.is_file():
            self.metadata_path = root_meta
        else:
            self.metadata_path = primary_meta

        self._cached_model: Optional[Any] = None
        self._cached_metadata: Optional[Dict[str, Any]] = None
        self._load_attempted: bool = False

    @property
    def feature_names(self) -> List[str]:
        metadata = self.get_metadata()
        return metadata.get('features', self.DEFAULT_FEATURE_NAMES)

    def is_available(self) -> bool:
        """Comprueba si el artefacto del modelo existe y está habilitado en los metadatos."""
        if self._cached_model is not None:
            return True
        if not self.model_path.is_file():
            return False
        meta = self.get_metadata()
        status = meta.get('status')
        available_flag = meta.get('available')
        if status == 'MODEL_NOT_AVAILABLE' or available_flag is False:
            return False
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Obtiene la metadata del modelo o retorna un estado descriptivo por defecto."""
        if self._cached_metadata is not None:
            return self._cached_metadata

        if self.metadata_path.is_file():
            try:
                with self.metadata_path.open('r', encoding='utf-8') as f:
                    self._cached_metadata = json.load(f)
                    return self._cached_metadata
            except Exception:
                pass

        msg = (
            'El modelo institucional todavía no ha sido entrenado. Requiere datos históricos del colegio.'
            if self.source == 'institutional'
            else 'El modelo de riesgo académico todavía no ha sido entrenado.'
        )
        return {
            'available': False,
            'version': None,
            'algorithm': None,
            'source': self.source,
            'trained_at': None,
            'features': self.DEFAULT_FEATURE_NAMES,
            'status': 'MODEL_NOT_AVAILABLE',
            'message': msg,
        }

    def get_model(self) -> Optional[Any]:
        """Carga el modelo serializado en memoria una sola vez (Singleton)."""
        if self._cached_model is not None:
            return self._cached_model

        if not self.is_available():
            return None

        try:
            self._cached_model = joblib.load(self.model_path)
            self._load_attempted = True
            return self._cached_model
        except Exception:
            self._cached_model = None
            return None

    def reload(self) -> None:
        """Limpia el caché forzando una recarga en la siguiente llamada."""
        self._cached_model = None
        self._cached_metadata = None
        self._load_attempted = False


_REGISTRY_INSTANCE: Optional[ModelRegistry] = None


def get_model_registry(base_dir: Optional[Path] = None, source: Optional[str] = None) -> ModelRegistry:
    global _REGISTRY_INSTANCE
    if _REGISTRY_INSTANCE is None or base_dir is not None or source is not None:
        _REGISTRY_INSTANCE = ModelRegistry(base_dir=base_dir, source=source)
    return _REGISTRY_INSTANCE
