from services.grading_policy_service import get_policy
from flask import Blueprint, jsonify, request, send_file

from services.db_service import fetch_all_topics, fetch_student_results, fetch_students
from services.teacher_export_service import build_excel_workbook, excel_filename
from services.teacher_reports_service import build_academic_report, build_report_summary, build_student_risk_analysis

teacher_reports_blueprint = Blueprint('teacher_reports', __name__, url_prefix='/teacher')


def _filters():
    grade = request.args.get('grade') or (request.get_json(silent=True) or {}).get('grade')
    section = request.args.get('section') or (request.get_json(silent=True) or {}).get('section') or 'all'
    period = request.args.get('period') or (request.get_json(silent=True) or {}).get('period') or '1'
    complete = str(request.args.get('complete') or (request.get_json(silent=True) or {}).get('complete') or '').lower() in {'1', 'true', 'yes'}
    grade_value = None if not grade or str(grade) == 'all' else int(grade)
    return grade_value, section, str(period), complete


@teacher_reports_blueprint.route('/api/reports/summary', methods=['GET'])
def api_reports_summary():
    students = fetch_students()
    topics = fetch_all_topics()
    summary = build_report_summary(students, topics)
    return jsonify(summary)


@teacher_reports_blueprint.route('/api/reports/gradebook', methods=['GET'])
def api_reports_gradebook():
    grade, section, period, _complete = _filters()
    report = build_academic_report(
        fetch_students(),
        fetch_student_results(),
        grade=grade,
        section=section,
        period=period,
        policy=get_policy(),
    )
    return jsonify({'success': True, **report})


@teacher_reports_blueprint.route('/api/reports/export.xlsx', methods=['GET'])
def api_export_excel_file():
    grade, section, period, complete = _filters()
    students = fetch_students()
    results = fetch_student_results()
    workbook = build_excel_workbook(
        students,
        results,
        grade=None if complete else grade,
        section=section,
        period=period,
        policy=get_policy(),
        complete=complete or not grade,
    )
    filename = excel_filename(grade, period, complete=complete or not grade)
    return send_file(
        workbook,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@teacher_reports_blueprint.route('/api/reports/student-risk', methods=['POST'])
def api_student_risk():
    payload = request.get_json() or {}
    student = payload.get('student', {})
    return jsonify(build_student_risk_analysis(student))
