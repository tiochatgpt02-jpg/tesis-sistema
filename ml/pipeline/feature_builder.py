"""Constructor canónico de características predictivas con aislamiento temporal estricto.

Garantiza la paridad exacta entre el pipeline de entrenamiento offline y el servicio
de inferencia en producción mediante la serialización de `features.json`.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

CANONICAL_FEATURES: List[str] = [
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


def parse_datetime(dt_val: Any) -> Optional[datetime]:
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val.astimezone(timezone.utc).replace(tzinfo=None) if dt_val.tzinfo else dt_val
    raw = str(dt_val).strip()
    if not raw:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
    except Exception:
        return None


def parse_cutoff(value):
    if value is None or value == '':
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError('La fecha de corte no es válida.')
    if isinstance(value,str) and len(value.strip()) == 10:
        parsed = parsed.replace(hour=23,minute=59,second=59,microsecond=999999)
    return parsed


def item_datetime(item):
    return parse_datetime(item.get('event_date') or item.get('created_at')
                          or item.get('submitted_at') or item.get('reviewed_at'))


def filter_by_cutoff(items: List[Dict[str, Any]], cutoff_dt: Optional[datetime]) -> List[Dict[str, Any]]:
    """Filtro anti-leakage: conserva únicamente eventos ocurridos antes o en el cutoff_dt."""
    if cutoff_dt is None:
        return list(items)
    filtered = []
    for item in items:
        dt = item_datetime(item)
        if dt is not None and dt <= cutoff_dt:
            filtered.append(item)
    return filtered


def extract_features_from_records(
    notes: List[Dict[str, Any]],
    submissions: Optional[List[Dict[str, Any]]] = None,
    materials_reviewed: Optional[List[Dict[str, Any]]] = None,
    cutoff_date: Union[str, datetime, None] = None,
) -> Dict[str, float]:
    """Calcula las 18 variables canónicas usando exclusivamente eventos <= cutoff_date."""
    cutoff_dt = parse_cutoff(cutoff_date)

    valid_notes = filter_by_cutoff(notes or [], cutoff_dt)
    valid_submissions = filter_by_cutoff(submissions or [], cutoff_dt)
    valid_reviews = filter_by_cutoff(materials_reviewed or [], cutoff_dt)

    # Orden cronológico
    valid_notes.sort(key=lambda x: item_datetime(x) or datetime.min)

    total_attempts = len(valid_notes)
    eval_notes = [n for n in valid_notes if str(n.get('activity_type', '')).lower() == 'evaluaciones']
    act_notes = [n for n in valid_notes if str(n.get('activity_type', '')).lower() == 'actividades']
    game_notes = [n for n in valid_notes if str(n.get('activity_type', '')).lower() == 'juegos']

    scores = []
    for n in valid_notes:
        try:
            raw = n.get('score')
            if raw is None or isinstance(raw,bool) or str(raw).strip() == '':
                raise ValueError()
            val = float(raw)
            if not math.isfinite(val) or not 0 <= val <= 20:
                raise ValueError()
            scores.append(val)
        except (ValueError, TypeError):
            raise ValueError('Las variables predictivas requieren notas numéricas finitas de 0 a 20.') from None

    eval_scores = [scores[i] for i, n in enumerate(valid_notes) if str(n.get('activity_type', '')).lower() == 'evaluaciones']
    act_scores = [scores[i] for i, n in enumerate(valid_notes) if str(n.get('activity_type', '')).lower() == 'actividades']

    avg_score = round(sum(scores) / total_attempts, 2) if total_attempts > 0 else 0.0
    avg_eval_score = round(sum(eval_scores) / len(eval_scores), 2) if eval_scores else 0.0
    avg_act_score = round(sum(act_scores) / len(act_scores), 2) if act_scores else 0.0

    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    last_score = scores[-1] if scores else 0.0

    # Desviación estándar
    if len(scores) >= 2:
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        score_std = round(math.sqrt(variance), 4)
    else:
        score_std = 0.0

    # Tendencia
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        score_trend = round(second_half - first_half, 2)
    elif len(scores) >= 2:
        score_trend = round(scores[-1] - scores[0], 2)
    else:
        score_trend = 0.0

    correct = sum(int(n.get('correct_answers', 0) or 0) for n in valid_notes)
    wrong = sum(int(n.get('wrong_answers', 0) or 0) for n in valid_notes)
    total_answers = correct + wrong
    accuracy = round(correct / total_answers, 4) if total_answers > 0 else 0.0

    times = [int(n.get('time_spent_seconds', 0) or 0) for n in valid_notes]
    avg_time = round(sum(times) / total_attempts, 2) if total_attempts > 0 else 0.0

    return {
        'total_attempts': float(total_attempts),
        'evaluation_count': float(len(eval_notes)),
        'activities_count': float(len(act_notes)),
        'games_count': float(len(game_notes)),
        'average_score': avg_score,
        'average_evaluation_score': avg_eval_score,
        'average_activity_score': avg_act_score,
        'min_score': min_score,
        'max_score': max_score,
        'last_score': last_score,
        'score_std': score_std,
        'score_trend': score_trend,
        'total_correct_answers': float(correct),
        'total_wrong_answers': float(wrong),
        'accuracy_ratio': accuracy,
        'average_time_spent_seconds': avg_time,
        'materials_reviewed_count': float(len(valid_reviews)),
        'submissions_count': float(len(valid_submissions)),
    }


def determine_target_risk(outcome: Dict[str, Any]) -> int:
    """Clasifica el resultado final en 1 (Riesgo Académico / Desaprobado) o 0 (Aprobado)."""
    if outcome.get('is_at_risk') is not None:
        try:
            number = float(outcome['is_at_risk'])
            if number not in (0,1):
                raise ValueError()
            return int(number)
        except (ValueError, TypeError):
            raise ValueError('El resultado de riesgo debe ser 0 o 1.') from None

    score = outcome.get('final_score')
    if score is not None:
        try:
            number = float(score)
            if not math.isfinite(number) or not 0 <= number <= 20:
                raise ValueError()
            if number < 11.0:
                return 1
            return 0
        except (ValueError, TypeError):
            raise ValueError('La nota final debe estar entre 0 y 20.') from None

    status = str(outcome.get('final_status', '')).strip().lower()
    if status in {'desaprobado', 'en_riesgo', 'reprobado', 'requiere_recuperacion', 'c'}:
        return 1
    if status in {'aprobado'}:
        return 0
    raise ValueError('Falta un resultado final verificado para definir el objetivo.')


def build_processed_matrix(
    source_csv: Path,
    output_csv: Path,
    cutoff_date: Optional[str] = None,
    features_json_path: Optional[Path] = None,
) -> int:
    """Genera la matriz procesada con X e y, y guarda features.json."""
    from ml.pipeline.data_loader import load_raw_csv

    records, quality_report = load_raw_csv(source_csv)

    student_notes = defaultdict(list)
    student_outcomes = {}
    student_meta = {}

    for r in records:
        code = r['student_code']
        observation = (r.get('academic_year'), r.get('period'), r.get('subject'))
        if code in student_meta and student_meta[code]['observation'] != observation:
            raise ValueError('No se pueden mezclar periodos o cursos de un mismo alumno. '
                             'Prepare una observacion con su corte y resultado posterior verificados.')
        if code not in student_meta:
            student_meta[code] = {
                'academic_year': r.get('academic_year'),
                'period': r.get('period'),
                'observation': observation,
            }

        if r.get('score') is not None:
            student_notes[code].append(r)

        if r.get('final_score') is not None or r.get('final_status') or r.get('is_at_risk') is not None:
            if code in student_outcomes and determine_target_risk(student_outcomes[code]) != determine_target_risk(r):
                raise ValueError('Hay resultados finales contradictorios para una misma observacion.')
            student_outcomes[code] = {
                'final_score': r.get('final_score'),
                'final_status': r.get('final_status'),
                'is_at_risk': r.get('is_at_risk'),
            }

    if not student_outcomes:
        raise ValueError(f"No se encontraron outcomes finales en {source_csv}")

    header = ['student_code', 'academic_year', 'period', 'cutoff_date'] + CANONICAL_FEATURES + ['target_risk']
    rows = []

    for code, out in student_outcomes.items():
        notes = student_notes.get(code, [])
        feats = extract_features_from_records(notes, cutoff_date=cutoff_date)
        if feats['total_attempts'] == 0:
            raise ValueError('No hay notas observadas antes del corte para una observacion con resultado final.')
        target = determine_target_risk(out)
        meta = student_meta.get(code, {})

        row = [
            code,
            meta.get('academic_year'),
            meta.get('period'),
            cutoff_date or '',
        ] + [feats.get(k, 0.0) for k in CANONICAL_FEATURES] + [target]
        rows.append(row)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    # Guardar features.json para consistencia de inferencia
    feat_dest = features_json_path or (output_csv.parent / 'features.json')
    with feat_dest.open('w', encoding='utf-8') as f:
        json.dump({
            'canonical_features': CANONICAL_FEATURES,
            'count': len(CANONICAL_FEATURES),
            'generated_at': datetime.now().isoformat(),
        }, f, indent=2)

    return len(rows)
