from __future__ import annotations

from typing import Any, Dict, Optional
from services.ml.prediction_service import get_risk_prediction_service


def build_prediction_payload(
    student_name: Optional[str] = None,
    score: Optional[float] = None,
    activity_type: str = 'actividades',
    student_id: Optional[int] = None,
    cutoff_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera la respuesta de predicción de riesgo académico.
    
    Si existe un modelo supervisado entrenado, ejecuta inferencia real.
    Si no existe un modelo entrenado, retorna una respuesta explícita
    con código MODEL_NOT_AVAILABLE sin inventar clasificaciones ni métricas.
    """
    name = (student_name or '').strip() or 'Estudiante'
    service = get_risk_prediction_service()

    if student_id is not None:
        prediction = service.predict_for_student(int(student_id), cutoff_date=cutoff_date)
        if prediction.get('success'):
            risk_level = prediction.get('risk_level', 'Bajo')
            level_map = {'Bajo': 'excelente', 'Medio': 'bueno', 'Alto': 'necesita apoyo'}
            level = level_map.get(risk_level, 'bueno')
            prob = prediction.get('risk_probability')
            prob_text = f" con probabilidad de riesgo estimada de {prob * 100:.1f}%" if prob is not None else ""
            summary = f"{name} clasificado con nivel de riesgo {risk_level}{prob_text} por modelo de Machine Learning supervisado."
            recommendation = (
                "Mantener el plan de trabajo actual y proponer desafíos complementarios." if risk_level == 'Bajo'
                else "Reforzar con actividades guiadas y seguimiento en las próximas sesiones." if risk_level == 'Medio'
                else "Alerta temprana: coordinar acompañamiento focalizado y tutoría personalizada."
            )
            return {
                'success': True,
                'student_id': int(student_id),
                'student_name': name,
                'score': round(float(score or 0), 2),
                'level': level,
                'risk_level': risk_level,
                'risk_probability': prob,
                'model_version': prediction.get('model_version', 'v1'),
                'model': prediction.get('model', {}),
                'main_factors': prediction.get('main_factors', []),
                'explanation': prediction.get('explanation', []),
                'recommendation': recommendation,
                'summary': summary,
            }
        else:
            return {
                'success': False,
                'code': 'MODEL_NOT_AVAILABLE',
                'status': 'MODEL_NOT_AVAILABLE',
                'message': (
                    'El modelo de riesgo académico todavía no ha sido entrenado. '
                    'Se requieren datos históricos reales del colegio para su entrenamiento.'
                ),
                'student_id': int(student_id),
                'student_name': name,
                'score': round(float(score or 0), 2),
                'level': 'No disponible',
                'risk_level': 'No disponible',
                'recommendation': 'El sistema está preparado para entrenar un modelo supervisado real en cuanto se proporcione el dataset institucional.',
                'summary': 'Modelo predictivo de Machine Learning no disponible. Pendiente de entrenamiento con datos reales.',
            }

    # Si no se pasó student_id, verificar disponibilidad del modelo
    if not service.is_available():
        return {
            'success': False,
            'code': 'MODEL_NOT_AVAILABLE',
            'status': 'MODEL_NOT_AVAILABLE',
            'message': (
                'El modelo de riesgo académico todavía no ha sido entrenado. '
                'Se requieren datos históricos reales del colegio para su entrenamiento.'
            ),
            'student_name': name,
            'score': round(float(score or 0), 2),
            'level': 'No disponible',
            'risk_level': 'No disponible',
            'recommendation': 'El sistema está preparado para entrenar un modelo supervisado real en cuanto se proporcione el dataset institucional.',
            'summary': 'Modelo predictivo de Machine Learning no disponible. Pendiente de entrenamiento con datos reales.',
        }

    # Modelo disponible sin student_id: inferencia usando características normalizadas
    from services.grade_service import normalize_to_scale_20
    score_20 = normalize_to_scale_20(score or 0)
    features = {
        'total_attempts': 1,
        'evaluation_count': 1 if activity_type == 'evaluaciones' else 0,
        'activities_count': 1 if activity_type == 'actividades' else 0,
        'games_count': 1 if activity_type == 'juegos' else 0,
        'average_score': score_20,
        'average_evaluation_score': score_20 if activity_type == 'evaluaciones' else 0.0,
        'average_activity_score': score_20 if activity_type == 'actividades' else 0.0,
        'min_score': score_20,
        'max_score': score_20,
        'last_score': score_20,
        'score_std': 0.0,
        'score_trend': 0.0,
        'total_correct_answers': 0,
        'total_wrong_answers': 0,
        'accuracy_ratio': 0.0,
        'average_time_spent_seconds': 0.0,
        'materials_reviewed_count': 0,
        'submissions_count': 0,
    }
    prediction = service.predict_for_features(features)
    risk_level = prediction.get('risk_level', 'Bajo')
    level_map = {'Bajo': 'excelente', 'Medio': 'bueno', 'Alto': 'necesita apoyo'}
    level = level_map.get(risk_level, 'bueno')
    prob = prediction.get('risk_probability')
    prob_text = f" con probabilidad de riesgo estimada de {prob * 100:.1f}%" if prob is not None else ""
    return {
        'success': True,
        'student_name': name,
        'score': round(score_20, 2),
        'level': level,
        'risk_level': risk_level,
        'risk_probability': prob,
        'model_version': prediction.get('model_version', 'v1'),
        'model': prediction.get('model', {}),
        'main_factors': prediction.get('main_factors', []),
        'explanation': prediction.get('explanation', []),
        'recommendation': (
            "Recomendación: mantener el ritmo de aprendizaje actual." if risk_level == 'Bajo'
            else "Recomendación: acompañar con actividades guiadas." if risk_level == 'Medio'
            else "Recomendación: priorizar refuerzo en áreas críticas."
        ),
        'summary': f"{name} presenta riesgo {risk_level}{prob_text}.",
    }


def predict_student_performance(progress: float, activity_type: str = 'actividades') -> Dict[str, Any]:
    """Evaluación formativa pedagógica determinista para retroalimentación en actividades.
    
    NO es Machine Learning; es una regla pedagógica transparente sin componentes
    aleatorios (eliminado random.uniform).
    """
    try:
        val = float(progress or 0)
    except (TypeError, ValueError):
        val = 0.0

    val = max(0.0, min(100.0, val))

    if val >= 80:
        level = 'excelente'
        advice = 'El estudiante demuestra dominio de las competencias y está listo para avanzar a temas de mayor complejidad.'
    elif val >= 55:
        level = 'bueno'
        advice = 'Buen progreso. Reforzar con práctica guiada y consolidación de conceptos clave.'
    else:
        level = 'necesita apoyo'
        advice = 'Se recomienda reforzar los temas fundamentales mediante actividades guiadas y acompañamiento docente.'

    return {
        'score': round(val, 2),
        'level': level,
        'advice': advice,
        'method': 'pedagogical_heuristic',
    }


def get_class_summary(students):
    if not students:
        return {'avg_progress': 0, 'total': 0}
    total = len(students)
    avg = sum(s.get('progress', 0) for s in students) // total
    return {'avg_progress': avg, 'total': total}

