import csv
import io

from flask import Response, render_template
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from lab5 import lab5_bp
from models import GUEST_USER_LABEL, User, VisitLog
from rights import VIEW_VISIT_REPORTS, check_rights


def _pages_report_rows():
    rows = (
        db.session.query(VisitLog.path, func.count(VisitLog.id).label('visit_count'))
        .group_by(VisitLog.path)
        .order_by(func.count(VisitLog.id).desc())
        .all()
    )
    return rows


def _users_report_rows():
    rows = (
        db.session.query(VisitLog.user_id, func.count(VisitLog.id).label('visit_count'))
        .group_by(VisitLog.user_id)
        .order_by(func.count(VisitLog.id).desc())
        .all()
    )
    result = []
    for user_id, visit_count in rows:
        if user_id is None:
            label = GUEST_USER_LABEL
        else:
            user = db.session.get(User, user_id)
            label = user.full_name if user and user.full_name else (
                user.login if user else GUEST_USER_LABEL
            )
        result.append((label, visit_count))
    return result


def _csv_response(filename, header, rows):
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


@lab5_bp.route('/reports/pages')
@login_required
@check_rights(VIEW_VISIT_REPORTS)
def report_pages():
    rows = _pages_report_rows()
    return render_template('lab5/report_pages.html', rows=rows)


@lab5_bp.route('/reports/users')
@login_required
@check_rights(VIEW_VISIT_REPORTS)
def report_users():
    rows = _users_report_rows()
    return render_template('lab5/report_users.html', rows=rows)


@lab5_bp.route('/reports/pages.csv')
@login_required
@check_rights(VIEW_VISIT_REPORTS)
def export_pages_csv():
    rows = _pages_report_rows()
    data = [(path, count) for path, count in rows]
    return _csv_response('report_pages.csv', ['Страница', 'Количество посещений'], data)


@lab5_bp.route('/reports/users.csv')
@login_required
@check_rights(VIEW_VISIT_REPORTS)
def export_users_csv():
    rows = _users_report_rows()
    data = [(label, count) for label, count in rows]
    return _csv_response('report_users.csv', ['Пользователь', 'Количество посещений'], data)
