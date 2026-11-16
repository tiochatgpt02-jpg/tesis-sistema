#!/usr/bin/env python3
"""Construye el dataset supervisado cruzando features previas al cutoff con el target posterior.

Diseñado estrictamente para evitar data leakage:
  - X: variables calculadas con eventos <= cutoff_date
  - y: target oficial ocurrido al final del periodo (almacenado en student_academic_outcomes)
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import db_service
from services.ml.feature_service import FeatureService
from services.ml.model_registry import ModelRegistry


def determine_target_risk(outcome: Dict[str, Any]) -> int:
    """Define si el outcome representa condición de riesgo académico (1) o éxito/aprobado (0)."""
    if outcome.get('is_at_risk') is not None:
        try:
            return int(outcome['is_at_risk'])
        except (ValueError, TypeError):
            pass

    status = str(outcome.get('final_status', '')).strip().lower()
    grade = outcome.get('final_score') if outcome.get('final_score') is not None else outcome.get('final_grade')

    # Si hay nota explícita < 11 en escala vigesimal
    if grade is not None:
        try:
            if float(grade) < 11.0:
                return 1
        except (ValueError, TypeError):
            pass

    # Si el estado es desaprobado, reprobado o en riesgo
    if status in {'desaprobado', 'en_riesgo', 'reprobado', 'requiere_recuperacion', 'c'}:
        return 1
    return 0


def build_dataset_from_csv(
    source_csv: Path,
    cutoff_date: str,
    output_path: Path,
    academic_year: int | None = None,
    period: str | None = None,
) -> int:
    from collections import defaultdict

    if not source_csv.is_file():
        raise FileNotFoundError(f"No se encontró el archivo CSV fuente: {source_csv}")

    student_notes = defaultdict(list)
    student_outcomes = {}
    student_meta = {}

    with source_csv.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('student_code') or str(row.get('student_id', ''))
            if not code:
                continue

            year_raw = row.get('academic_year')
            period_raw = row.get('period')
            try:
                row_year = int(year_raw) if year_raw else None
            except ValueError:
                row_year = None

            if academic_year is not None and row_year != academic_year:
                continue
            if period is not None and period_raw != period:
                continue

            if code not in student_meta:
                student_meta[code] = {
                    'student_code': code,
                    'academic_year': row_year,
                    'period': period_raw,
                }

            score_raw = row.get('score')
            if score_raw is not None and str(score_raw).strip() != '':
                try:
                    score_val = float(str(score_raw).strip())
                    student_notes[code].append({
                        'score': score_val,
                        'activity_type': row.get('activity_type', 'actividades'),
                        'created_at': row.get('event_date'),
                    })
                except ValueError:
                    pass

            final_score_raw = row.get('final_score')
            final_status_raw = row.get('final_status')
            is_risk_raw = row.get('is_at_risk')
            if final_score_raw or final_status_raw or is_risk_raw is not None:
                student_outcomes[code] = {
                    'final_score': float(final_score_raw) if final_score_raw else None,
                    'final_status': final_status_raw,
                    'is_at_risk': int(is_risk_raw) if is_risk_raw is not None and str(is_risk_raw).strip() != '' else None,
                }

    if not student_outcomes:
        print(f"No se encontraron outcomes válidos en: {source_csv}")
        return 0

    print(f"Procesando {len(student_outcomes)} estudiantes desde CSV con fecha de corte: {cutoff_date}...")
    feature_names = ModelRegistry.DEFAULT_FEATURE_NAMES
    header = ['student_id', 'student_code', 'academic_year', 'period', 'cutoff_date'] + feature_names + ['target_risk']

    rows = []
    for idx, (code, out) in enumerate(student_outcomes.items(), start=1):
        notes = student_notes.get(code, [])
        features = FeatureService.extract_features_from_records(notes=notes, cutoff_date=cutoff_date)
        target = determine_target_risk(out)
        meta = student_meta.get(code, {})

        row = [
            idx,
            code,
            meta.get('academic_year'),
            meta.get('period'),
            cutoff_date,
        ] + [features.get(k, 0.0) for k in feature_names] + [target]
        rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Dataset generado exitosamente en: {output_path}")
    print(f"Total de observaciones: {len(rows)}")
    positives = sum(r[-1] for r in rows)
    print(f"Distribución del target: Riesgo={positives} ({(positives/len(rows))*100:.1f}%), Sin Riesgo={len(rows)-positives}")
    return len(rows)


def build_training_dataset(
    cutoff_date: str,
    output_path: Path,
    academic_year: int | None = None,
    period: str | None = None,
    source_csv: Path | None = None,
) -> int:
    if source_csv is not None:
        return build_dataset_from_csv(
            source_csv=source_csv,
            cutoff_date=cutoff_date,
            output_path=output_path,
            academic_year=academic_year,
            period=period,
        )

    outcomes = db_service.fetch_academic_outcomes(academic_year=academic_year, period=period)
    if not outcomes:
        print("No se encontraron registros en 'student_academic_outcomes'.")
        print("Debe importar datos históricos reales usando: python ml/scripts/import_historical_data.py <archivo.csv>")
        return 0

    print(f"Procesando {len(outcomes)} outcomes con fecha de corte: {cutoff_date}...")
    feature_names = ModelRegistry.DEFAULT_FEATURE_NAMES
    header = ['student_id', 'academic_year', 'period', 'cutoff_date'] + feature_names + ['target_risk']

    rows = []
    for out in outcomes:
        student_id = int(out['student_id'])
        features = FeatureService.extract_features_for_student(student_id, cutoff_date=cutoff_date)
        target = determine_target_risk(out)

        year = out.get('academic_year')
        period_val = out.get('period')
        if (not year or not period_val) and out.get('academic_period') and '-' in str(out['academic_period']):
            parts = str(out['academic_period']).split('-', 1)
            year = year or parts[0]
            period_val = period_val or parts[1]

        row = [
            student_id,
            year,
            period_val,
            cutoff_date,
        ] + [features.get(k, 0.0) for k in feature_names] + [target]
        rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Dataset generado exitosamente en: {output_path}")
    print(f"Total de observaciones: {len(rows)}")
    positives = sum(r[-1] for r in rows)
    print(f"Distribución del target: Riesgo={positives} ({(positives/len(rows))*100:.1f}%), Sin Riesgo={len(rows)-positives}")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Construye matriz de entrenamiento a partir de outcomes y cutoff temporal.")
    parser.add_argument("--cutoff-date", type=str, required=True, help="Fecha de corte (YYYY-MM-DD) para variables predictivas.")
    parser.add_argument("--output", type=Path, default=ROOT / "ml" / "datasets" / "processed" / "training_dataset.csv", help="Ruta de salida del CSV.")
    parser.add_argument("--source-csv", type=Path, default=None, help="Ruta a CSV institucional opcional para construir directamente sin base de datos.")
    parser.add_argument("--year", type=int, default=None, help="Año académico a filtrar.")
    parser.add_argument("--period", type=str, default=None, help="Periodo/Bimestre a filtrar.")
    args = parser.parse_args()

    build_training_dataset(
        cutoff_date=args.cutoff_date,
        output_path=args.output,
        academic_year=args.year,
        period=args.period,
        source_csv=args.source_csv,
    )


if __name__ == '__main__':
    main()
