#!/usr/bin/env python3
"""Script institucional para importar datos históricos académicos desde un archivo CSV.

Permite cargar simultáneamente:
1. Eventos y calificaciones históricas previas al corte temporal (almacenadas en student_notes).
2. Resultados finales del período o target académico oficial (almacenados en student_academic_outcomes).

Soporta variables externas (como asistencia) de manera totalmente opcional.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Agregar raíz del proyecto al path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import db_service
from services.grade_service import normalize_to_scale_20


REQUIRED_COLUMNS = {'academic_year', 'period'}
IDENTIFIER_COLUMNS = {'student_code', 'student_id'}
VALID_STATUSES = {
    'aprobado', 'desaprobado', 'en_riesgo', 'promovido',
    'reprobado', 'requiere_recuperacion', 'ad', 'a', 'b', 'c'
}


def normalize_activity_type(raw_type: Optional[str]) -> str:
    """Normaliza el tipo de actividad a los valores canónicos del sistema."""
    t = str(raw_type or '').strip().lower()
    if any(keyword in t for keyword in ('evalua', 'examen', 'test', 'quiz', 'parcial')):
        return 'evaluaciones'
    if any(keyword in t for keyword in ('juego', 'game', 'ludic', 'gamif')):
        return 'juegos'
    return 'actividades'


def validate_row(row: Dict[str, Any], row_num: int) -> Tuple[bool, str, Dict[str, Any]]:
    """Valida los tipos, rangos y consistencia de cada fila del CSV."""
    # 1. Identificador de estudiante (student_code o student_id)
    student_code = str(row.get('student_code') or '').strip()
    student_id_raw = row.get('student_id')

    if not student_code and not student_id_raw:
        return False, f"Fila {row_num}: Debe incluir 'student_code' o 'student_id'", {}

    student_id: Optional[int] = None
    if student_id_raw:
        try:
            student_id = int(str(student_id_raw).strip())
        except (ValueError, TypeError):
            return False, f"Fila {row_num}: student_id debe ser un entero", {}

    # 2. Año académico
    try:
        academic_year = int(str(row.get('academic_year', '')).strip())
        if academic_year < 2000 or academic_year > 2100:
            return False, f"Fila {row_num}: academic_year inválido ({academic_year})", {}
    except (ValueError, TypeError):
        return False, f"Fila {row_num}: academic_year debe ser un año válido de 4 dígitos", {}

    # 3. Período / Bimestre
    period = str(row.get('period', '')).strip()
    if not period:
        return False, f"Fila {row_num}: period no puede estar vacío", {}

    # 4. Curso / Materia
    subject = str(row.get('subject', 'Computación')).strip() or 'Computación'

    # 5. Fecha del evento formativo (opcional)
    event_date_raw = str(row.get('event_date', '')).strip()
    event_date: Optional[str] = None
    if event_date_raw:
        try:
            # Validar formato de fecha (YYYY-MM-DD o ISO)
            if 'T' in event_date_raw or ' ' in event_date_raw:
                parsed_dt = datetime.fromisoformat(event_date_raw.replace(' ', 'T'))
            else:
                parsed_dt = datetime.strptime(event_date_raw, '%Y-%m-%d')
            event_date = parsed_dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False, f"Fila {row_num}: event_date con formato inválido ('{event_date_raw}'). Use YYYY-MM-DD", {}

    # 6. Calificación del evento (opcional)
    score_raw = row.get('score')
    score: Optional[float] = None
    if score_raw is not None and str(score_raw).strip() != '':
        try:
            score = float(str(score_raw).strip())
            if score < 0.0 or score > 20.0:
                return False, f"Fila {row_num}: score debe estar en escala vigesimal (0 a 20). Recibido: {score}", {}
        except ValueError:
            return False, f"Fila {row_num}: score no numérico: '{score_raw}'", {}

    # 7. Asistencia opcional (0 a 100)
    attendance_raw = row.get('attendance_percentage')
    attendance_percentage: Optional[float] = None
    if attendance_raw is not None and str(attendance_raw).strip() != '':
        try:
            attendance_percentage = float(str(attendance_raw).strip())
            if attendance_percentage < 0.0 or attendance_percentage > 100.0:
                return False, f"Fila {row_num}: attendance_percentage debe estar entre 0 y 100", {}
        except ValueError:
            return False, f"Fila {row_num}: attendance_percentage no numérico: '{attendance_raw}'", {}

    # 8. Nota final de período (outcome opcional)
    final_score_raw = row.get('final_score') or row.get('final_grade')
    final_score: Optional[float] = None
    if final_score_raw is not None and str(final_score_raw).strip() != '':
        try:
            final_score = float(str(final_score_raw).strip())
            if final_score < 0.0 or final_score > 20.0:
                return False, f"Fila {row_num}: final_score debe estar en escala vigesimal (0 a 20). Recibido: {final_score}", {}
        except ValueError:
            return False, f"Fila {row_num}: final_score no numérico: '{final_score_raw}'", {}

    # 9. Estado final de período (outcome opcional)
    final_status = str(row.get('final_status', '')).strip().lower() or None

    # 10. Etiqueta explícita de riesgo (opcional)
    is_at_risk_raw = row.get('is_at_risk')
    is_at_risk: Optional[int] = None
    if is_at_risk_raw is not None and str(is_at_risk_raw).strip() != '':
        try:
            is_at_risk = int(str(is_at_risk_raw).strip())
            if is_at_risk not in (0, 1):
                return False, f"Fila {row_num}: is_at_risk debe ser 0 o 1", {}
        except ValueError:
            return False, f"Fila {row_num}: is_at_risk debe ser 0 o 1", {}

    # Verificar que la fila aporte al menos un dato (evento formativo u outcome)
    has_event = score is not None
    has_outcome = (final_score is not None) or (final_status is not None) or (is_at_risk is not None)
    if not has_event and not has_outcome:
        return False, f"Fila {row_num}: La fila no contiene ni calificación de evento ni datos de outcome final", {}

    cleaned = {
        'student_code': student_code or (f"ALU-{student_id:04d}" if student_id else 'ALU-0001'),
        'student_id': student_id,
        'academic_year': academic_year,
        'period': period,
        'subject': subject,
        'event_date': event_date,
        'activity_type': normalize_activity_type(row.get('activity_type')),
        'score': score,
        'attendance_percentage': attendance_percentage,
        'final_score': final_score,
        'final_status': final_status,
        'is_at_risk': is_at_risk,
    }
    return True, '', cleaned


def import_csv(csv_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Importa registros históricos académicos verificando esquema, eventos y outcomes."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Archivo no encontrado: {csv_path}")

    valid_records: List[Dict[str, Any]] = []
    errors: List[str] = []

    with csv_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("El archivo CSV está vacío o no contiene encabezados.")

        field_set = {c.strip() for c in reader.fieldnames}
        missing_required = REQUIRED_COLUMNS - field_set
        if missing_required:
            raise ValueError(f"Faltan columnas obligatorias en el CSV: {sorted(missing_required)}")

        has_ident = any(id_col in field_set for id_col in IDENTIFIER_COLUMNS)
        if not has_ident:
            raise ValueError("El CSV debe incluir al menos una columna de identificación: 'student_code' o 'student_id'.")

        for i, row in enumerate(reader, start=2):
            ok, msg, clean_row = validate_row(row, i)
            if ok:
                valid_records.append(clean_row)
            else:
                errors.append(msg)

    print(f"\n--- Validación de CSV Institucional ---")
    print(f"Total registros analizados: {len(valid_records) + len(errors)}")
    print(f"Registros válidos:          {len(valid_records)}")
    print(f"Registros con error:        {len(errors)}")

    if errors:
        print("\nErrores de validación detectados:")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... y {len(errors) - 10} errores adicionales.")

    notes_inserted = 0
    outcomes_inserted = 0

    if not dry_run and valid_records:
        for record in valid_records:
            # 1. Obtener o registrar estudiante
            student_id = record['student_id']
            if student_id is None:
                student_id = db_service.fetch_or_create_student_by_code(record['student_code'])

            # 2. Registrar evento formativo en student_notes (si tiene score)
            if record['score'] is not None:
                try:
                    event_dt = record['event_date'] or f"{record['academic_year']}-01-01 00:00:00"
                    db_service.record_student_result(
                        student_id=student_id,
                        topic_id=None,
                        activity_type=record['activity_type'],
                        item_type='historical_record',
                        score=record['score'],
                        correct_answers=0,
                        wrong_answers=0,
                        time_spent_seconds=0,
                        created_at=event_dt,
                    )
                    notes_inserted += 1
                except Exception as exc:
                    print(f"Aviso al insertar nota de estudiante {student_id}: {exc}")

            # 3. Registrar o actualizar outcome final en student_academic_outcomes
            has_outcome_data = (
                record['final_score'] is not None or
                record['final_status'] is not None or
                record['is_at_risk'] is not None
            )
            if has_outcome_data:
                academic_period = f"{record['academic_year']}-{record['period']}"
                final_score_val = record['final_score'] if record['final_score'] is not None else (record['score'] or 0.0)

                if record['is_at_risk'] is not None:
                    at_risk = int(record['is_at_risk'])
                elif record['final_score'] is not None and float(record['final_score']) < 11.0:
                    at_risk = 1
                elif record['final_status'] in {'desaprobado', 'en_riesgo', 'reprobado', 'requiere_recuperacion', 'c'}:
                    at_risk = 1
                else:
                    at_risk = 0

                risk_level = 'Alto' if at_risk == 1 else 'Bajo'
                reason = f"Estado final: {record['final_status']}" if record['final_status'] else None

                try:
                    db_service.insert_academic_outcome(
                        student_id=student_id,
                        academic_period=academic_period,
                        period_type='bimester',
                        final_score=final_score_val,
                        attendance_percentage=record['attendance_percentage'],
                        is_at_risk=at_risk,
                        risk_level=risk_level,
                        risk_reasons=reason,
                        academic_year=record['academic_year'],
                        period=record['period'],
                        subject=record['subject'],
                        final_status=record['final_status'],
                    )
                    outcomes_inserted += 1
                except Exception as exc:
                    print(f"Aviso al registrar outcome del estudiante {student_id}: {exc}")

        print(f"\nImportación completada con éxito:")
        print(f"  - Calificaciones/eventos formativos importados: {notes_inserted}")
        print(f"  - Outcomes académicos finales registrados:      {outcomes_inserted}")
    elif dry_run:
        print("\nModo --dry-run activo: los registros son válidos pero no se modificó la base de datos.")

    return {
        'total': len(valid_records) + len(errors),
        'valid': len(valid_records),
        'rejected': len(errors),
        'notes_inserted': notes_inserted,
        'outcomes_inserted': outcomes_inserted,
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Importa historial académico institucional desde archivo CSV.")
    parser.add_argument("csv_file", type=Path, help="Ruta al archivo CSV con datos históricos.")
    parser.add_argument("--dry-run", action="store_true", help="Valida el formato sin persistir en la base de datos.")
    args = parser.parse_args()

    try:
        import_csv(args.csv_file, dry_run=args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

