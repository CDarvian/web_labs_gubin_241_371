from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Role, User
from rights import (
    CREATE_USER,
    DELETE_USER,
    EDIT_USER,
    VIEW_USER,
    VIEW_VISIT_LOG,
    check_rights,
    user_has_right,
)
from validators import (
    validate_change_password,
    validate_create_user,
    validate_edit_user,
)

lab4_bp = Blueprint('lab4', __name__, url_prefix='/lab4')


@lab4_bp.context_processor
def lab4_context():
    def can_create_user():
        return user_has_right(current_user, CREATE_USER)

    def can_view_user(target):
        return user_has_right(current_user, VIEW_USER, target)

    def can_edit_user(target):
        return user_has_right(current_user, EDIT_USER, target)

    def can_delete_user(target):
        return user_has_right(current_user, DELETE_USER, target)

    def can_view_visit_log():
        return user_has_right(current_user, VIEW_VISIT_LOG)

    return {
        'can_create_user': can_create_user,
        'can_view_user': can_view_user,
        'can_edit_user': can_edit_user,
        'can_delete_user': can_delete_user,
        'can_view_visit_log': can_view_visit_log,
    }


def _get_roles():
    return Role.query.order_by(Role.name).all()


def _parse_role_id(raw_role_id):
    if not raw_role_id:
        return None
    try:
        return int(raw_role_id)
    except (TypeError, ValueError):
        return None


def _form_data_from_request(include_credentials=False):
    data = {
        'surname': request.form.get('surname', ''),
        'first_name': request.form.get('first_name', ''),
        'patronymic': request.form.get('patronymic', ''),
        'role_id': request.form.get('role_id', ''),
    }
    if include_credentials:
        data['login'] = request.form.get('login', '')
        data['password'] = request.form.get('password', '')
    return data


@lab4_bp.route('/')
def index():
    users = User.query.order_by(User.id).all()
    return render_template('lab4/index.html', users=users)


@lab4_bp.route('/users/<int:user_id>')
@login_required
@check_rights(VIEW_USER, user_kwarg='user_id')
def view_user(user_id):
    user = db.session.get(User, user_id)
    return render_template('lab4/view.html', user=user)


@lab4_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@check_rights(CREATE_USER)
def create_user():
    roles = _get_roles()
    form_data = _form_data_from_request(include_credentials=True)
    field_errors = {}

    if request.method == 'POST':
        field_errors = validate_create_user(form_data)
        if not field_errors:
            role_id = _parse_role_id(form_data.get('role_id'))
            user = User(
                login=form_data['login'].strip(),
                surname=form_data['surname'].strip() or None,
                first_name=form_data['first_name'].strip(),
                patronymic=form_data['patronymic'].strip() or None,
                role_id=role_id,
            )
            user.set_password(form_data['password'])
            db.session.add(user)
            try:
                db.session.commit()
                flash('Пользователь успешно создан.', 'success')
                return redirect(url_for('lab4.index'))
            except IntegrityError:
                db.session.rollback()
                field_errors['login'] = 'Пользователь с таким логином уже существует'
                flash('Ошибка при создании пользователя.', 'danger')

    return render_template(
        'lab4/create.html',
        roles=roles,
        form_data=form_data,
        field_errors=field_errors,
    )


@lab4_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@check_rights(EDIT_USER, user_kwarg='user_id')
def edit_user(user_id):
    user = db.session.get(User, user_id)
    roles = _get_roles()
    field_errors = {}
    can_change_role = current_user.is_admin

    if request.method == 'POST':
        form_data = _form_data_from_request()
        field_errors = validate_edit_user(form_data)
        if not field_errors:
            user.surname = form_data['surname'].strip() or None
            user.first_name = form_data['first_name'].strip()
            user.patronymic = form_data['patronymic'].strip() or None
            if can_change_role:
                user.role_id = _parse_role_id(form_data.get('role_id'))
            try:
                db.session.commit()
                flash('Данные пользователя успешно обновлены.', 'success')
                return redirect(url_for('lab4.index'))
            except IntegrityError:
                db.session.rollback()
                flash('Ошибка при обновлении пользователя.', 'danger')
    else:
        form_data = {
            'surname': user.surname or '',
            'first_name': user.first_name or '',
            'patronymic': user.patronymic or '',
            'role_id': str(user.role_id) if user.role_id else '',
        }

    return render_template(
        'lab4/edit.html',
        user=user,
        roles=roles,
        form_data=form_data,
        field_errors=field_errors,
        can_change_role=can_change_role,
    )


@lab4_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@check_rights(DELETE_USER, user_kwarg='user_id')
def delete_user(user_id):
    user = db.session.get(User, user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удалён.', 'success')
    except Exception:
        db.session.rollback()
        flash('Ошибка при удалении пользователя.', 'danger')

    return redirect(url_for('lab4.index'))


@lab4_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lab4.index'))

    if request.method == 'POST':
        login_value = request.form.get('login', '')
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(login=login_value).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Успешный вход!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('lab4.index'))
        flash('Неверный логин или пароль.', 'danger')

    return render_template('lab4/login.html')


@lab4_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('lab4.index'))


@lab4_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form_data = {
        'old_password': '',
        'new_password': '',
        'confirm_password': '',
    }
    field_errors = {}

    if request.method == 'POST':
        form_data = {
            'old_password': request.form.get('old_password', ''),
            'new_password': request.form.get('new_password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
        }
        field_errors = validate_change_password(
            form_data['old_password'],
            form_data['new_password'],
            form_data['confirm_password'],
            current_user,
        )
        if not field_errors:
            current_user.set_password(form_data['new_password'])
            db.session.commit()
            flash('Пароль успешно изменён.', 'success')
            return redirect(url_for('lab4.index'))

    return render_template(
        'lab4/change_password.html',
        form_data=form_data,
        field_errors=field_errors,
    )
