#!/usr/bin/env python3
"""Descarga y convierte el dataset benchmark internacional abierto de la UCI (Student Performance)

Fuente: UCI Machine Learning Repository / Cortez and Silva, 2008
Cursos: Matemática (student-mat) y Lengua Portuguesa / Humanidades (student-por)
Escala: Vigesimal original (0 a 20).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
import shutil
import sys
import urllib.request
from typing import Any, Dict, List, Tuple

ROOT = Path(r"c:\Users\familia\Downloads\sistema IA\sistema IA")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

URL_MAT = "https://raw.githubusercontent.com/guipsamora/pandas_exercises/master/04_Apply/Students_Alcohol_Consumption/student-mat.csv"
URL_POR = "https://raw.githubusercontent.com/KunjalJethwani/StudentPerformance/master/student-por.csv"


def fetch_csv_data(url: str) -> List[Dict[str, str]]:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8')
    
    # Detect delimiter (comma or semicolon)
    first_line = content.split('\n', 1)[0]
    delimiter = ';' if ';' in first_line else ','
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    return list(reader)


def prepare_benchmark_csv(output_csv: Path) -> int:
    print("--- Descargando Benchmark UCI Student Performance ---")
    raw_mat = fetch_csv_data(URL_MAT)
    print(f"Matemática (student-mat): {len(raw_mat)} estudiantes descargados.")
    raw_por = fetch_csv_data(URL_POR)
    print(f"Humanidades (student-por): {len(raw_por)} estudiantes descargados.")

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    header = [
        'student_code',
        'academic_year',
        'period',
        'subject',
        'event_date',
        'activity_type',
        'score',
        'attendance_percentage',
        'final_score',
        'final_status',
        'is_at_risk',
    ]

    records: List[List[Any]] = []
    student_counter = 1

    datasets = [
        (raw_mat, 'Matemática', 'MAT'),
        (raw_por, 'Comunicación', 'POR'),
    ]

    for data, subject_name, prefix in datasets:
        total_in_subset = len(data)
        for idx, row in enumerate(data):
            code = f"ALU-BM-{prefix}-{idx+1:04d}"
            
            # Asignar 60% de estudiantes al año 2023 y 40% al año 2024
            # Esto permite una división temporal natural (entrenar en 2023, evaluar en 2024)
            year = 2023 if idx < int(total_in_subset * 0.6) else 2024
            period = 'B1'

            g1 = float(row.get('G1', 0))
            g2 = float(row.get('G2', 0))
            g3 = float(row.get('G3', 0))
            absences = float(row.get('absences', 0))
            attendance_pct = max(0.0, min(100.0, round(100.0 - (absences * 2.5), 1)))

            at_risk = 1 if g3 < 11.0 else 0
            final_status = 'desaprobado' if at_risk == 1 else 'aprobado'

            # Evento formativo 1: Evaluación intermedia del primer tercio (marzo)
            records.append([
                code,
                year,
                period,
                subject_name,
                f"{year}-03-20 10:00:00",
                'actividades',
                g1,
                '',   # Asistencia no obligatoria en evento
                '',
                '',
                '',
            ])

            # Evento formativo 2: Evaluación intermedia del segundo tercio (abril) + Outcome final consolidado
            records.append([
                code,
                year,
                period,
                subject_name,
                f"{year}-04-25 10:00:00",
                'evaluaciones',
                g2,
                attendance_pct,
                g3,
                final_status,
                at_risk,
            ])
            student_counter += 1

    with output_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(records)

    total_students = len(raw_mat) + len(raw_por)
    print(f"\nArchivo institucional generado con éxito en: {output_csv}")
    print(f"Total de estudiantes convertidos: {total_students}")
    print(f"Total de filas generadas (eventos + outcomes): {len(records)}")

    # Copiar también al repo de ml/scripts
    script_dest = ROOT / "ml" / "scripts" / "download_and_prepare_benchmark.py"
    shutil.copy(__file__, script_dest)
    print(f"Script copiado a: {script_dest}")

    return len(records)


def main():
    dest = ROOT / "ml" / "datasets" / "raw" / "uci_student_performance_institutional.csv"
    prepare_benchmark_csv(dest)


if __name__ == '__main__':
    main()
