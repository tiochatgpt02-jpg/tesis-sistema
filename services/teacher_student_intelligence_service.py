from typing import Any, Dict, List


def analyze_student_performance(student: Dict[str, Any], notes: List[Dict[str, Any]]) -> Dict[str, Any]:
    average = sum(float(item.get('score', 0) or 0) for item in notes or []) / max(1, len(notes or []))
    strengths = ['Participa con constancia en actividades prácticas.']
    difficulties = []
    reinforce = []

    if average >= 15:
        risk_level = 'bajo'
        strengths.append('Tiene buen dominio de los temas trabajados.')
    elif average >= 10:
        risk_level = 'medio'
        difficulties.append('Presenta algunas dudas en la aplicación de conceptos.')
        reinforce.append('Word')
    else:
        risk_level = 'alto'
        difficulties.append('Necesita reforzar contenidos básicos y practicar con más frecuencia.')
        reinforce.append('Word')

    if not notes:
        risk_level = 'medio'
        difficulties.append('No hay suficiente evidencia de desempeño reciente.')

    return {
        'student_name': f"{student.get('first_name', 'Estudiante')} {student.get('last_name', '')}".strip(),
        'fortalezas': strengths,
        'dificultades': difficulties or ['Sin dificultades detectadas en la evidencia disponible.'],
        'temas_a_reforzar': reinforce or ['Tema general'],
        'nivel_rendimiento': 'alto' if average >= 15 else 'medio' if average >= 10 else 'bajo',
        'risk_level': risk_level,
        'recomendaciones': [
            'Se recomienda reforzar actividades prácticas del tema principal.',
            'Mantener seguimiento semanal con evaluaciones cortas.',
        ],
        'average_score': round(average, 2),
    }
