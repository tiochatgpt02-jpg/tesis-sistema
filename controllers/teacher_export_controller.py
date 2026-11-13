from io import BytesIO
from flask import Blueprint, send_file
from services.db_service import fetch_students, fetch_student_results
from services.teacher_export_service import build_excel_workbook
from services.grading_policy_service import get_policy

teacher_export_blueprint = Blueprint('teacher_export', __name__, url_prefix='/teacher')

@teacher_export_blueprint.route('/api/reports/export/excel', methods=['POST'])
def api_export_excel():
    data = build_excel_workbook(fetch_students(), fetch_student_results(), complete=True, policy=get_policy())
    return send_file(data, download_name='reporte.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@teacher_export_blueprint.route('/api/reports/export/pdf', methods=['POST'])
def api_export_pdf():
    from reportlab.pdfgen import canvas
    from services.teacher_reports_service import build_student_grade_rows
    buffer = BytesIO()
    document = canvas.Canvas(buffer)
    document.setTitle('Reporte de rendimiento')
    y = 800
    for row in build_student_grade_rows(fetch_students(), fetch_student_results(), get_policy()):
        document.drawString(40,y,f"{row['student_name'][:65]}: {row['average'] if row['average'] is not None else 'Pendiente'}")
        y -= 20
        if y < 50:
            document.showPage()
            y = 800
    document.save()
    buffer.seek(0)
    return send_file(buffer, download_name='reporte.pdf', as_attachment=True, mimetype='application/pdf')
