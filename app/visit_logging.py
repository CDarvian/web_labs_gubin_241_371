from flask import request
from flask_login import current_user

from extensions import db
from models import VisitLog


def register_visit_logging(app):
    @app.before_request
    def log_visit():
        if request.method != 'GET':
            return
        if request.path == '/favicon.ico':
            return
        if request.endpoint and request.endpoint.startswith('static'):
            return

        user_id = None
        if current_user.is_authenticated:
            user_id_str = current_user.get_id()
            if isinstance(user_id_str, str) and user_id_str.startswith('db_'):
                try:
                    user_id = int(user_id_str[3:])
                except (TypeError, ValueError):
                    user_id = None

        visit = VisitLog(path=request.path[:100], user_id=user_id)
        try:
            db.session.add(visit)
            db.session.commit()
        except Exception:
            db.session.rollback()
