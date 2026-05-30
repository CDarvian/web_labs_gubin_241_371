from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

from extensions import db
from models import User

INSUFFICIENT_RIGHTS_MESSAGE = (
    'У вас недостаточно прав для доступа к данной странице.'
)

CREATE_USER = 'create_user'
EDIT_USER = 'edit_user'
VIEW_USER = 'view_user'
DELETE_USER = 'delete_user'
VIEW_VISIT_LOG = 'view_visit_log'
VIEW_VISIT_REPORTS = 'view_visit_reports'


def user_has_right(user, action, target_user=None):
    if not user.is_authenticated or not hasattr(user, 'is_admin'):
        return False

    if action == CREATE_USER:
        return user.is_admin
    if action == EDIT_USER:
        if target_user is None:
            return False
        return user.is_admin or user.id == target_user.id
    if action == VIEW_USER:
        if target_user is None:
            return False
        return user.is_admin or user.id == target_user.id
    if action == DELETE_USER:
        return user.is_admin
    if action == VIEW_VISIT_LOG:
        return True
    if action == VIEW_VISIT_REPORTS:
        return user.is_admin

    return False


def _redirect_insufficient_rights():
    flash(INSUFFICIENT_RIGHTS_MESSAGE, 'danger')
    return redirect(url_for('lab4.index'))


def check_rights(action, user_kwarg=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            target_user = None
            if user_kwarg is not None:
                user_id = kwargs.get(user_kwarg)
                if user_id is None:
                    return _redirect_insufficient_rights()
                target_user = db.session.get(User, user_id)
                if target_user is None:
                    flash('Пользователь не найден.', 'danger')
                    return redirect(url_for('lab4.index'))

            if not user_has_right(current_user, action, target_user):
                return _redirect_insufficient_rights()

            return view_func(*args, **kwargs)

        return wrapped

    return decorator
