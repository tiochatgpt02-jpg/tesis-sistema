from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union



class FeatureService:
    """Extrae características tabulares a partir de registros académicos previos al corte temporal."""

    @staticmethod
    def _parse_cutoff(value):
        from ml.pipeline.feature_builder import parse_cutoff
        return parse_cutoff(value)

    @staticmethod
    def _parse_item_datetime(item):
        from ml.pipeline.feature_builder import item_datetime
        return item_datetime(item)

    @staticmethod
    def filter_by_cutoff(items, cutoff_dt):
        from ml.pipeline.feature_builder import filter_by_cutoff
        return filter_by_cutoff(items, cutoff_dt)

    @staticmethod
    def extract_features_from_records(notes, submissions=None, materials_reviewed=None, cutoff_date=None):
        from ml.pipeline.feature_builder import extract_features_from_records
        return extract_features_from_records(notes, submissions, materials_reviewed, cutoff_date)

    @classmethod
    def extract_features_for_student(
        cls,
        student_id: int,
        cutoff_date: Union[str, datetime, None] = None,
    ) -> Dict[str, Any]:
        """Consulta la base de datos y extrae las features de un estudiante sin superar el cutoff temporal."""
        from services import db_service

        # An unavailable database must not be reported as an empty student history.
        notes = db_service.fetch_student_results(student_id=student_id) or []
        submissions = db_service.fetch_submissions(student_id=student_id) or []
        if db_service._use_mock():
            reviews = [{'material_id': material_id, 'student_id': int(student_id)}
                       for material_id in db_service._MOCK_MATERIAL_REVIEWS.get(int(student_id), set())]
        else:
            reviews = db_service._query(
                'SELECT material_id, student_id, reviewed_at FROM material_reviews WHERE student_id = %s',
                (int(student_id),),
            ) or []

        return cls.extract_features_from_records(
            notes=notes,
            submissions=submissions,
            materials_reviewed=reviews,
            cutoff_date=cutoff_date,
        )


def extract_features_for_student(
    student_id: int, cutoff_date: Union[str, datetime, None] = None
) -> Dict[str, Any]:
    return FeatureService.extract_features_for_student(student_id, cutoff_date)
