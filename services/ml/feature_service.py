from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Union

from services.grade_service import normalize_to_scale_20


class FeatureService:
    """Extrae características tabulares a partir de registros académicos previos al corte temporal."""

    @staticmethod
    def _parse_cutoff(cutoff_date: Union[str, datetime, None]) -> Optional[datetime]:
        if cutoff_date is None:
            return None
        if isinstance(cutoff_date, datetime):
            return cutoff_date
        raw = str(cutoff_date).strip()
        if not raw:
            return None
        # Admite formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
        try:
            if 'T' in raw or ' ' in raw:
                cleaned = raw.replace(' ', 'T')
                return datetime.fromisoformat(cleaned)
            return datetime.strptime(raw, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_item_datetime(item: Dict[str, Any]) -> Optional[datetime]:
        dt = item.get('created_at') or item.get('submitted_at') or item.get('reviewed_at')
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt
        try:
            raw = str(dt).strip().replace(' ', 'T')
            return datetime.fromisoformat(raw)
        except Exception:
            return None

    @classmethod
    def filter_by_cutoff(
        cls, items: List[Dict[str, Any]], cutoff_dt: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        if cutoff_dt is None:
            return list(items or [])
        filtered = []
        for item in items or []:
            item_dt = cls._parse_item_datetime(item)
            if item_dt is None or item_dt <= cutoff_dt:
                filtered.append(item)
        return filtered

    @classmethod
    def extract_features_from_records(
        cls,
        notes: List[Dict[str, Any]],
        submissions: Optional[List[Dict[str, Any]]] = None,
        materials_reviewed: Optional[List[Dict[str, Any]]] = None,
        cutoff_date: Union[str, datetime, None] = None,
    ) -> Dict[str, Any]:
        """Calcula el vector de variables predictivas usando única y exclusivamente eventos <= cutoff_date."""
        cutoff_dt = cls._parse_cutoff(cutoff_date)

        # Filtrado estricto anti-leakage
        valid_notes = cls.filter_by_cutoff(notes, cutoff_dt)
        valid_submissions = cls.filter_by_cutoff(submissions or [], cutoff_dt)
        valid_reviews = cls.filter_by_cutoff(materials_reviewed or [], cutoff_dt)

        # Ordenar notas cronológicamente
        valid_notes.sort(
            key=lambda x: cls._parse_item_datetime(x) or datetime.min
        )

        total_attempts = len(valid_notes)
        eval_notes = [n for n in valid_notes if str(n.get('activity_type')).lower() == 'evaluaciones']
        act_notes = [n for n in valid_notes if str(n.get('activity_type')).lower() == 'actividades']
        game_notes = [n for n in valid_notes if str(n.get('activity_type')).lower() == 'juegos']

        scores = [normalize_to_scale_20(n.get('score')) for n in valid_notes]
        eval_scores = [normalize_to_scale_20(n.get('score')) for n in eval_notes]
        act_scores = [normalize_to_scale_20(n.get('score')) for n in act_notes]

        correct_answers = sum(int(n.get('correct_answers', 0) or 0) for n in valid_notes)
        wrong_answers = sum(int(n.get('wrong_answers', 0) or 0) for n in valid_notes)
        total_answers = correct_answers + wrong_answers
        accuracy_ratio = round(correct_answers / total_answers, 4) if total_answers > 0 else 0.0

        times = [int(n.get('time_spent_seconds', 0) or 0) for n in valid_notes]
        avg_time = round(sum(times) / total_attempts, 2) if total_attempts > 0 else 0.0

        avg_score = round(sum(scores) / total_attempts, 2) if total_attempts > 0 else 0.0
        avg_eval_score = round(sum(eval_scores) / len(eval_scores), 2) if eval_scores else 0.0
        avg_act_score = round(sum(act_scores) / len(act_scores), 2) if act_scores else 0.0

        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        last_score = scores[-1] if scores else 0.0

        # Desviación estándar de notas
        if len(scores) >= 2:
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            score_std = round(math.sqrt(variance), 4)
        else:
            score_std = 0.0

        # Tendencia de notas: diferencia entre promedio de la 2da mitad y la 1ra mitad
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
            score_trend = round(second_half_avg - first_half_avg, 2)
        elif len(scores) >= 2:
            score_trend = round(scores[-1] - scores[0], 2)
        else:
            score_trend = 0.0

        return {
            'total_attempts': total_attempts,
            'evaluation_count': len(eval_notes),
            'activities_count': len(act_notes),
            'games_count': len(game_notes),
            'average_score': avg_score,
            'average_evaluation_score': avg_eval_score,
            'average_activity_score': avg_act_score,
            'min_score': min_score,
            'max_score': max_score,
            'last_score': last_score,
            'score_std': score_std,
            'score_trend': score_trend,
            'total_correct_answers': correct_answers,
            'total_wrong_answers': wrong_answers,
            'accuracy_ratio': accuracy_ratio,
            'average_time_spent_seconds': avg_time,
            'materials_reviewed_count': len(valid_reviews),
            'submissions_count': len(valid_submissions),
        }

    @classmethod
    def extract_features_for_student(
        cls,
        student_id: int,
        cutoff_date: Union[str, datetime, None] = None,
    ) -> Dict[str, Any]:
        """Consulta la base de datos y extrae las features de un estudiante sin superar el cutoff temporal."""
        from services import db_service

        try:
            notes = db_service.fetch_student_results(student_id=student_id) or []
        except Exception:
            notes = []

        try:
            submissions = db_service.fetch_submissions(student_id=student_id) or []
        except Exception:
            submissions = []

        reviews: List[Dict[str, Any]] = []
        try:
            reviews = db_service._query(
                'SELECT material_id, student_id, reviewed_at FROM material_reviews WHERE student_id = %s',
                (int(student_id),),
            ) or []
        except Exception:
            reviews = []

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
