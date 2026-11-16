"""Cargador y validador de datos para el pipeline de Machine Learning escolar.

Responsable de:
  - Carga de archivos CSV crudos e institucionales.
  - Validación estricta de columnas obligatorias.
  - Validación de tipos de datos, formatos de fecha y rangos en escala vigesimal (0-20).
  - Carga segura de matrices procesadas con exclusión garantizada de identificadores personales en X.
"""

from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Set
import numpy as np

# Columnas obligatorias para el CSV de eventos académicos crudos
MANDATORY_EVENT_COLUMNS: List[str] = [
    'student_code',
    'academic_year',
    'period',
    'subject',
    'event_date',
    'activity_type',
    'score',
    'final_status',
]

DISALLOWED_IN_X: Set[str] = {
    'student_id', 'student_code', 'id', 'user_id', 'codigo_estudiante', 'dni',
    'first_name', 'last_name', 'email', 'phone', 'academic_year', 'period',
    'academic_period', 'cutoff_date', 'target_risk', 'target', 'risk_level',
    'is_at_risk', 'final_status', 'final_score', 'final_grade', 'student_name'
}


def validate_event_columns(fieldnames: List[str]) -> None:
    """Valida la presencia de todas las columnas requeridas en el CSV crudo."""
    if not fieldnames:
        raise ValueError("El archivo CSV no contiene cabecera ni nombres de columna.")
    
    clean_fields = {f.strip() for f in fieldnames}
    missing = [col for col in MANDATORY_EVENT_COLUMNS if col not in clean_fields]
    if missing:
        raise ValueError(
            f"Validación fallida: Faltan columnas obligatorias en el archivo CSV: {missing}. "
            f"Columnas requeridas: {MANDATORY_EVENT_COLUMNS}"
        )


def parse_date_safely(date_str: Any) -> Optional[datetime]:
    """Parsea una fecha en diversos formatos estándares."""
    if not date_str:
        return None
    raw = str(date_str).strip()
    if not raw:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def load_raw_csv(csv_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Carga y valida un archivo CSV de eventos académicos formativos e históricos.
    
    Retorna:
      Tuple[registros_validados, reporte_de_calidad]
    Lanza:
      FileNotFoundError si el archivo no existe.
      ValueError si faltan columnas obligatorias o el archivo está vacío.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV en: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"El archivo {path} no contiene columnas o está vacío.")
        validate_event_columns(reader.fieldnames)

        invalid_rows = 0
        missing_values = 0
        students_seen: Set[str] = set()

        for line_num, r in enumerate(reader, start=2):
            code = (r.get('student_code') or '').strip()
            if not code:
                invalid_rows += 1
                continue
            students_seen.add(code)

            # Validar año
            year_val = r.get('academic_year')
            try:
                year_int = int(year_val) if year_val else None
                if year_int is not None and (year_int < 1900 or year_int > 2100):
                    invalid_rows += 1
                    continue
            except (ValueError, TypeError):
                invalid_rows += 1
                continue

            # Validar nota si está presente en la fila
            score_val = r.get('score')
            score_float: Optional[float] = None
            if score_val is not None and str(score_val).strip() != '':
                try:
                    score_float = float(str(score_val).strip())
                    if not math.isfinite(score_float) or score_float < 0.0 or score_float > 20.0:
                        invalid_rows += 1
                        continue
                except ValueError:
                    invalid_rows += 1
                    continue
            else:
                missing_values += 1

            # Validar fecha
            event_date_str = r.get('event_date')
            dt = parse_date_safely(event_date_str)

            rows.append({
                'student_code': code,
                'academic_year': year_int,
                'period': (r.get('period') or '').strip(),
                'subject': (r.get('subject') or 'General').strip(),
                'event_date': dt.isoformat() if dt else event_date_str,
                'activity_type': (r.get('activity_type') or 'actividades').strip().lower(),
                'score': score_float,
                'final_status': (r.get('final_status') or '').strip(),
                'final_score': float(r['final_score']) if r.get('final_score') and str(r.get('final_score')).strip() != '' else None,
                'is_at_risk': int(r['is_at_risk']) if r.get('is_at_risk') is not None and str(r.get('is_at_risk')).strip() != '' else None,
                'attendance_percentage': float(r['attendance_percentage']) if r.get('attendance_percentage') and str(r.get('attendance_percentage')).strip() != '' else None,
            })

    if not rows:
        raise ValueError(f"El archivo {path} no contiene registros válidos.")

    quality_report = {
        'total_rows_read': len(rows) + invalid_rows,
        'valid_events': len(rows),
        'unique_students': len(students_seen),
        'missing_values': missing_values,
        'invalid_rows': invalid_rows,
    }

    return rows, quality_report


def load_training_matrix(
    csv_path: Path,
    feature_names: Optional[List[str]] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str], List[Dict[str, Any]]]:
    """Carga la matriz predictiva procesada X, target y, grupos y metadatos.
    
    Asegura por aserción la exclusión total de identificadores de X.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de matriz procesada no encontrado: {path}")

    rows: List[Dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("El archivo procesado no contiene columnas.")
        for r in reader:
            rows.append(r)

    if not rows:
        raise ValueError(f"El dataset procesado en {path} está vacío.")

    available_cols = reader.fieldnames or []
    if feature_names is not None:
        active_features = [f for f in feature_names if f in available_cols and f.lower() not in DISALLOWED_IN_X]
    else:
        # Detectar columnas numéricas excluyendo identificadores y targets
        active_features = [
            col for col in available_cols
            if col.lower() not in DISALLOWED_IN_X
        ]

    if not active_features:
        raise ValueError("No se encontraron características predictivas válidas en la matriz.")

    # Verificación estricta de seguridad anti-leakage de identificadores personales
    for col in active_features:
        col_lower = col.lower()
        if col_lower in DISALLOWED_IN_X or 'student' in col_lower or 'codigo' in col_lower or 'dni' in col_lower:
            raise ValueError(
                f"Violación crítica de integridad: La columna '{col}' es un identificador o metadato "
                "y bajo ninguna circunstancia debe ingresar a la matriz de entrenamiento X."
            )

    X_list: List[List[float]] = []
    y_list: List[int] = []
    groups_list: List[str] = []
    metadata_list: List[Dict[str, Any]] = []

    for idx, r in enumerate(rows):
        feat_vec = []
        for feat in active_features:
            val = r.get(feat)
            if val is None or str(val).strip() == '' or str(val).strip().lower() == 'nan':
                feat_vec.append(np.nan)
            else:
                try:
                    feat_vec.append(float(str(val).strip()))
                except ValueError:
                    feat_vec.append(np.nan)

        target_raw = next((r[key] for key in ('target_risk','is_at_risk','target')
                           if r.get(key) is not None and str(r[key]).strip() != ''),None)
        try:
            number = float(str(target_raw).strip())
            if number not in (0,1):
                raise ValueError()
            target = int(number)
        except (ValueError, TypeError):
            raise ValueError('Cada fila de entrenamiento requiere un resultado binario verificado de 0 o 1.') from None

        student_code = (r.get('student_code') or str(r.get('student_id', idx))).strip()
        year = r.get('academic_year')
        period = r.get('period')
        acad_period = r.get('academic_period') or (f"{year}-{period}" if year and period else str(year or '2024-B1'))

        X_list.append(feat_vec)
        y_list.append(target)
        groups_list.append(student_code)
        metadata_list.append({
            'student_id': r.get('student_id') or idx,
            'student_code': student_code,
            'academic_year': year,
            'period': period,
            'academic_period': acad_period,
            'cutoff_date': r.get('cutoff_date'),
        })

    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)
    groups = np.array(groups_list)

    return X, y, groups, active_features, metadata_list
