"""Prepare a single-course UCI reference, without invented historical cohorts."""
from __future__ import annotations
import argparse
import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
import math
from pathlib import Path
import requests
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
SOURCE_URL='https://archive.ics.uci.edu/static/public/320/student+performance.zip'
DATASET_URL='https://archive.ics.uci.edu/dataset/320/student+performance'


def course_csv(archive):
    with ZipFile(BytesIO(archive)) as outer:
        if 'student-por.csv' in outer.namelist():
            return outer.read('student-por.csv')
        if 'student.zip' in outer.namelist():
            with ZipFile(BytesIO(outer.read('student.zip'))) as inner:
                return inner.read('student-por.csv')
    raise ValueError('El archivo oficial no contiene student-por.csv.')


def prepare_benchmark_csv(output_csv: Path, archive_path: Path | None = None) -> int:
    if archive_path is None:
        response=requests.get(SOURCE_URL,headers={'User-Agent':'AulaComputacionTesis/1.0'},timeout=60)
        response.raise_for_status()
        archive=response.content
        if len(archive)>5_000_000:
            raise ValueError('El archivo de referencia excede el limite esperado.')
    else:
        archive=Path(archive_path).read_bytes()
    raw=course_csv(archive)
    rows=list(csv.DictReader(StringIO(raw.decode('utf-8-sig')),delimiter=';'))
    if not rows or not {'G1','G2','G3'}.issubset(rows[0]):
        raise ValueError('Faltan las tres calificaciones del curso de referencia.')
    records=[]
    for index,row in enumerate(rows,1):
        grades=[float(row[key]) for key in ('G1','G2','G3')]
        if any(not math.isfinite(value) or not 0<=value<=20 for value in grades):
            raise ValueError('Calificacion invalida en el archivo de referencia.')
        g1,g2,g3=grades
        identity=f'UCI-POR-{index:04d}'
        # Artificial timestamps express G1 before G2, not actual collection dates.
        records.append([identity,2000,'UCI','Portuguese','2000-01-01','actividades',g1,'','',''])
        records.append([identity,2000,'UCI','Portuguese','2000-02-01','evaluaciones',g2,g3,
                        'desaprobado' if g3<11 else 'aprobado',int(g3<11)])
    output_csv=Path(output_csv)
    output_csv.parent.mkdir(parents=True,exist_ok=True)
    with output_csv.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream)
        writer.writerow(['student_code','academic_year','period','subject','event_date','activity_type',
                         'score','final_score','final_status','is_at_risk'])
        writer.writerows(records)
    provenance={'name':'UCI Student Performance','source_url':SOURCE_URL,'dataset_url':DATASET_URL,
        'course':'student-por.csv','observations':len(rows),'events':len(records),
        'archive_sha256':sha256(archive).hexdigest(),'course_sha256':sha256(raw).hexdigest(),
        'events_sha256':sha256(output_csv.read_bytes()).hexdigest(),
        'synthetic_event_dates':True,'chronological_cohorts':False,
        'purpose':'Technical reference only, not institutional validation',
        'label_rule':'G3 < 11, project convention, not an official conversion of AD/A/B/C',
        'license':'CC BY 4.0; attribute UCI Student Performance and Paulo Cortez'}
    output_csv.with_name('dataset_metadata.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps({'course':provenance['course'],'observations':len(rows),'events':len(records),
                      'synthetic_event_dates':True,'cohorts':'not historical'}))
    return len(records)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'ml/datasets/benchmark/raw/uci_student_performance_events.csv')
    parser.add_argument('--archive',type=Path)
    options=parser.parse_args()
    prepare_benchmark_csv(options.output,options.archive)

if __name__=='__main__':
    main()
