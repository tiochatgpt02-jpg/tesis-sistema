#!/usr/bin/env python3
"""Importador institucional validado de datos académicos escolares.

Acepta y valida archivos CSV institucionales con:
  - Columnas obligatorias: student_code, academic_year, period, subject, event_date, activity_type, score, final_status
  - Escala vigesimal oficial (0 a 20)
  - Fechas cronológicas válidas
  - Detección de duplicados

Genera:
  - import_report.json
  - Actualización de dataset_metadata.json institucional
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.pipeline.data_loader import MANDATORY_EVENT_COLUMNS, parse_date_safely, validate_event_columns


def import_school_dataset(
    input_csv: Path,
    output_csv: Path,
    report_path: Path,
    dry_run: bool = False,
) -> Dict[str, Any]:
    input_p = Path(input_csv)
    if not input_p.is_file():
        raise FileNotFoundError(f"No se encontró el archivo institucional en: {input_p}")

    with input_p.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("El archivo está vacío o no contiene cabecera de columnas.")
        validate_event_columns(reader.fieldnames)
        raw_rows = list(reader)

    valid_events = []
    seen_students: Set[str] = set()
    seen_fingerprints: Set[str] = set()
    invalid_rows = 0
    missing_values = 0
    duplicate_rows = 0

    canonical_headers = [
        'student_code', 'academic_year', 'period', 'subject',
        'event_date', 'activity_type', 'score', 'final_status',
        'final_score', 'is_at_risk', 'attendance_percentage'
    ]

    for line_idx, row in enumerate(raw_rows, start=2):
        code = (row.get('student_code') or '').strip()
        if not code:
            invalid_rows += 1
            continue

        year_raw = row.get('academic_year')
        try:
            year = int(year_raw) if year_raw else None
            if year is not None and (year < 1900 or year > 2100):
                invalid_rows += 1
                continue
        except (ValueError, TypeError):
            invalid_rows += 1
            continue

        score_raw = row.get('score')
        score_val = None
        if score_raw is not None and str(score_raw).strip() != '':
            try:
                score_val = float(str(score_raw).strip())
                if score_val < 0.0 or score_val > 20.0:
                    invalid_rows += 1
                    continue
            except ValueError:
                invalid_rows += 1
                continue
        else:
            missing_values += 1

        dt = parse_date_safely(row.get('event_date'))
        dt_str = dt.isoformat() if dt else (row.get('event_date') or '').strip()

        # Comprobar duplicados exactos de evento
        period_str = (row.get('period') or '').strip()
        subject_str = (row.get('subject') or 'General').strip()
        act_str = (row.get('activity_type') or 'actividades').strip().lower()

        fingerprint = f"{code}|{year}|{period_str}|{subject_str}|{dt_str}|{act_str}|{score_val}"
        if fingerprint in seen_fingerprints:
            duplicate_rows += 1
            continue
        seen_fingerprints.add(fingerprint)
        seen_students.add(code)

        valid_events.append({
            'student_code': code,
            'academic_year': year,
            'period': period_str,
            'subject': subject_str,
            'event_date': dt_str,
            'activity_type': act_str,
            'score': score_val if score_val is not None else '',
            'final_status': (row.get('final_status') or '').strip(),
            'final_score': row.get('final_score') or '',
            'is_at_risk': row.get('is_at_risk') or '',
            'attendance_percentage': row.get('attendance_percentage') or '',
        })

    report = {
        'students': len(seen_students),
        'events': len(valid_events),
        'missing_values': missing_values,
        'invalid_rows': invalid_rows,
        'duplicate_rows': duplicate_rows,
        'imported_at': datetime.now().isoformat(),
        'source_file': str(input_p),
        'status': 'VALIDATED' if len(valid_events) > 0 else 'EMPTY',
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if not dry_run and valid_events:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=canonical_headers)
            writer.writeheader()
            writer.writerows(valid_events)

        # Actualizar dataset_metadata.json institucional
        meta_inst_path = ROOT / "ml" / "datasets" / "institutional" / "dataset_metadata.json"
        if meta_inst_path.is_file():
            try:
                with meta_inst_path.open('r', encoding='utf-8') as f:
                    meta_inst = json.load(f)
                meta_inst.update({
                    'samples': len(seen_students),
                    'total_events': len(valid_events),
                    'updated_at': datetime.now().isoformat(),
                    'status': 'DATA_READY',
                })
                with meta_inst_path.open('w', encoding='utf-8') as f:
                    json.dump(meta_inst, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    print(f"\n--- Reporte de Importación Institucional ---")
    print(f"Estudiantes procesados: {report['students']}")
    print(f"Eventos válidos:        {report['events']}")
    print(f"Valores faltantes:      {report['missing_values']}")
    print(f"Filas inválidas:        {report['invalid_rows']}")
    print(f"Duplicados descartados: {report['duplicate_rows']}")
    print(f"Reporte guardado en:    {report_path}")
    if not dry_run:
        print(f"Dataset guardado en:    {output_csv}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Importa y valida el dataset institucional del colegio.")
    parser.add_argument("--input", type=Path, required=True, help="Ruta al CSV con historial escolar.")
    parser.add_argument("--output", type=Path, default=ROOT / "ml" / "datasets" / "institutional" / "raw" / "school_academic_history.csv", help="Destino CSV.")
    parser.add_argument("--report", type=Path, default=ROOT / "ml" / "datasets" / "institutional" / "raw" / "import_report.json", help="Destino de reporte JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Solo validar y generar reporte sin guardar datos.")
    args = parser.parse_args()

    try:
        import_school_dataset(
            input_csv=args.input,
            output_csv=args.output,
            report_path=args.report,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR al importar dataset institucional: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
