from __future__ import annotations

import csv
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.teacher_reports_service import GRADE_LABELS, build_academic_report
from services.grading_policy_service import COMPONENTS


EXCEL_COLUMNS = [
    ('n', 'N.º'),
    ('code', 'Código'),
    ('student_name', 'Alumno'),
    ('grade', 'Grado'),
    ('activities', 'Actividades'),
    ('evaluations', 'Evaluaciones'),
    ('average', 'Promedio'),
    ('level', 'Nivel de logro'),
]


def _write_sheet(workbook, title: str, rows: List[Dict[str, Any]], subtitle: str = '', components=False):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    sheet = workbook.create_sheet(title[:31])
    header_fill = PatternFill('solid', fgColor='1D4ED8')
    header_font = Font(color='FFFFFF', bold=True)
    title_font = Font(bold=True, size=14, color='1E3A8A')
    thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )
    level_fills = {
        'AD': PatternFill('solid', fgColor='BBF7D0'),
        'A': PatternFill('solid', fgColor='BFDBFE'),
        'B': PatternFill('solid', fgColor='FDE68A'),
        'C': PatternFill('solid', fgColor='FECACA'),
    }

    columns = EXCEL_COLUMNS[:4] + list(COMPONENTS) + EXCEL_COLUMNS[-2:] if components else EXCEL_COLUMNS
    last_column = get_column_letter(len(columns))
    sheet.merge_cells(f'A1:{last_column}1')
    sheet['A1'] = title
    sheet['A1'].font = title_font
    if subtitle:
        sheet.merge_cells(f'A2:{last_column}2')
        sheet['A2'] = subtitle

    header_row = 4 if subtitle else 3
    for index, (_key, label) in enumerate(columns, start=1):
        cell = sheet.cell(header_row, index, label)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin

    for row_index, row in enumerate(rows, start=header_row + 1):
        values = [f"{row.get('grade')}°" if key == 'grade' else
                  row.get('components', {}).get(key) if components and key in dict(COMPONENTS) else row.get(key)
                  for key, _ in columns]
        for col, value in enumerate(values, start=1):
            cell = sheet.cell(row_index, col, value)
            cell.border = thin
            cell.alignment = Alignment(horizontal='center' if col != 3 else 'left')
            if col == len(columns):
                cell.fill = level_fills.get(str(value), PatternFill())
                cell.font = Font(bold=True)

    widths = [8, 14, 28, 12] + ([19] * 6 if components else [14, 16]) + [12, 16]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.auto_filter.ref = f'A{header_row}:{last_column}{header_row + max(len(rows), 1)}'
    sheet.freeze_panes = f'A{header_row + 1}'
    return sheet


def build_excel_workbook(
    students: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    grade: Optional[int] = None,
    section: Optional[str] = None,
    period: str = '1',
    complete: bool = False,
    policy=None,
) -> BytesIO:
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)

    if complete or not grade:
        summary_rows = []
        for grade_value in (4, 5, 6):
            report = build_academic_report(students, results, grade=grade_value, section=section, period=period, policy=policy)
            _write_sheet(
                workbook,
                GRADE_LABELS[grade_value],
                report['rows'],
                f"{report['period_label']} · Promedio {report['average']}",
                components=bool(policy and policy.get('mode') == 'components'),
            )
            summary_rows.append({
                'n': grade_value - 3,
                'code': f'{grade_value}°',
                'student_name': GRADE_LABELS[grade_value],
                'grade': grade_value,
                'activities': report['students_count'],
                'evaluations': report['counts']['destacado'] + report['counts']['esperado'],
                'average': report['average'],
                'level': f"AD {report['counts']['destacado']} / A {report['counts']['esperado']} / B {report['counts']['proceso']} / C {report['counts']['apoyo']}",
            })
        _write_sheet(workbook, 'Resumen general', summary_rows, 'Consolidado de 4.º, 5.º y 6.º')
    else:
        report = build_academic_report(students, results, grade=grade, section=section, period=period, policy=policy)
        _write_sheet(
            workbook,
            GRADE_LABELS.get(int(grade), f'{grade}° Primaria'),
            report['rows'],
            f"{report['period_label']} · Promedio {report['average']}",
            components=bool(policy and policy.get('mode') == 'components'),
        )

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def excel_filename(grade: Optional[int], period: str, complete: bool = False) -> str:
    period_label = f'Bimestre_{period or 1}'
    if complete or not grade:
        return f'Reporte_completo_{period_label}.xlsx'
    slug = {4: '4to', 5: '5to', 6: '6to'}.get(int(grade), f'{grade}to')
    return f'Notas_{slug}_Primaria_{period_label}.xlsx'


def generate_excel_report(rows: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['student', 'grado', 'tema', 'nota'])
        writer.writeheader()
        writer.writerows(rows)
    return {'status': 'ok', 'path': str(path)}


def generate_pdf_report(rows: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ['Reporte de rendimiento', '====================']
    for row in rows:
        content.append(f"{row.get('student', 'Estudiante')} | {row.get('grado', '')} | {row.get('tema', '')} | Nota: {row.get('nota', 0)}")
    path.write_text('\n'.join(content), encoding='utf-8')
    return {'status': 'ok', 'path': str(path)}
