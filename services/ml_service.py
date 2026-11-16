from __future__ import annotations

from typing import Any, Dict, Optional
from services.ml.prediction_service import get_risk_prediction_service


def _unavailable_payload(prediction, name, score, student_id=None):
    no_history = prediction.get('code') == 'INSUFFICIENT_HISTORY' or prediction.get('risk_level') == 'Sin datos'
    message = ('Registra prácticas y evaluaciones para disponer de historial académico.' if no_history else
               prediction.get('message') or 'No se pudo obtener una predicción válida. No se ha asignado riesgo.')
    return {
        'success': bool(no_history), 'code': prediction.get('code', 'PREDICTION_ERROR'),
        'status': prediction.get('code', 'PREDICTION_ERROR'), 'message': message,
        'student_id': student_id, 'student_name': name, 'score': round(float(score or 0), 2),
        'level': 'Sin datos' if no_history else 'No disponible',
        'risk_level': 'Sin datos' if no_history else 'No disponible',
        'risk_probability': None, 'predicted_class': None,
        'model': prediction.get('model', {}), 'main_factors': prediction.get('main_factors', []),
        'explanation': prediction.get('explanation', []),
        'recommendation': message, 'summary': message,
    }


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
        if not prediction.get('success') or prediction.get('risk_probability') is None:
            return _unavailable_payload(prediction, name, score, int(student_id))
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
                'validation_scope': prediction.get('validation_scope'),
                'notice': prediction.get('notice'),
                'main_factors': prediction.get('main_factors', []),
                'explanation': prediction.get('explanation', []),
                'recommendation': recommendation,
                'summary': summary,
            }

    return _unavailable_payload({
        'code': 'STUDENT_REQUIRED',
        'message': 'Selecciona un alumno para consultar su historial. Una nota aislada no basta para construir una prediccion academica.',
    }, name, score)


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

