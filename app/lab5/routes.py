from flask import render_template, request
from flask_login import current_user, login_required

from extensions import db
from lab5 import lab5_bp
from models import VisitLog
from rights import VIEW_VISIT_LOG, check_rights

PER_PAGE = 20


def _visit_log_query():
    query = VisitLog.query.order_by(VisitLog.created_at.desc())
    if current_user.is_authenticated and not current_user.is_admin:
        query = query.filter(VisitLog.user_id == current_user.id)
    return query


@lab5_bp.route('/')
@login_required
@check_rights(VIEW_VISIT_LOG)
def index():
    page = request.args.get('page', 1, type=int)
    pagination = _visit_log_query().paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template(
        'lab5/index.html',
        logs=pagination.items,
        pagination=pagination,
        per_page=PER_PAGE,
    )
