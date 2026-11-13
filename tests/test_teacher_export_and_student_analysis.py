import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.teacher_export_service import build_excel_workbook, generate_excel_report, generate_pdf_report
from services.teacher_student_intelligence_service import analyze_student_performance


def test_analyze_student_performance_identifies_strengths_and_risks():
    analysis = analyze_student_performance(
        student={'first_name': 'Ana', 'last_name': 'Martínez', 'grade': 5},
        notes=[
            {'activity_type': 'actividades', 'score': 18, 'topic': 'Word'},
            {'activity_type': 'evaluaciones', 'score': 12, 'topic': 'Word'},
            {'activity_type': 'juegos', 'score': 16, 'topic': 'Word'},
        ],
    )
    assert 'fortalezas' in analysis
    assert 'dificultades' in analysis
    assert analysis['risk_level'] in {'bajo', 'medio', 'alto'}


def test_generate_excel_report_creates_file(tmp_path):
    dest = tmp_path / 'reporte.xlsx'
    result = generate_excel_report([
        {'student': 'Ana', 'grado': 5, 'tema': 'Word', 'nota': 18},
    ], str(dest))
    assert result['status'] == 'ok'
    assert dest.exists()


def test_generate_pdf_report_creates_file(tmp_path):
    dest = tmp_path / 'reporte.pdf'
    result = generate_pdf_report([
        {'student': 'Ana', 'grado': 5, 'tema': 'Word', 'nota': 18},
    ], str(dest))
    assert result['status'] == 'ok'
    assert dest.exists()


def test_build_excel_workbook_generates_xlsx_with_rows():
    workbook = build_excel_workbook(
        students=[
            {'id': 1, 'student_code': 'A-001', 'first_name': 'Ana', 'last_name': 'López', 'grade': 5, 'section': 'A'},
            {'id': 2, 'student_code': 'A-002', 'first_name': 'Luis', 'last_name': 'Pérez', 'grade': 5, 'section': 'A'},
        ],
        results=[
            {'student_id': 1, 'activity_type': 'actividades', 'score': 18},
            {'student_id': 1, 'activity_type': 'evaluaciones', 'score': 17},
            {'student_id': 2, 'activity_type': 'actividades', 'score': 16},
            {'student_id': 2, 'activity_type': 'evaluaciones', 'score': 15},
        ],
        grade=5,
        section='A',
        period='1',
        complete=False,
    )
    assert workbook is not None
    data = workbook.getvalue()
    assert len(data) > 0
    assert data.startswith(b'PK')
