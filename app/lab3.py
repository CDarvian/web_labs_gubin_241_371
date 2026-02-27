from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user

lab3_bp = Blueprint('lab3', __name__, url_prefix='/lab3')


# Класс пользователя для Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# Хардкодим пользователя из задания
users_db = {
    "user": User("1", "user", "qwerty")
}


@lab3_bp.route('/')
def index():
    return render_template('lab3/index.html')


@lab3_bp.route('/counter')
def counter():
    # Используем глобальный объект session для счетчика
    session['visits'] = session.get('visits', 0) + 1
    return render_template('lab3/counter.html', visits=session['visits'])


@lab3_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lab3.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'  # Чекбокс "Запомнить меня"

        user = users_db.get(username)
        if user and user.password == password:
            login_user(user, remember=remember)
            flash('Успешный вход!', 'success')

            # Перенаправляем на 'next' (если пришли с закрытой страницы) или на главную
            next_page = request.args.get('next')
            return redirect(next_page or url_for('lab3.index'))
        else:
            flash('Неверный логин или пароль.', 'danger')

    return render_template('lab3/login.html')


@lab3_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('lab3.index'))


@lab3_bp.route('/secret')
@login_required  # Доступ только для авторизованных
def secret():
    return render_template('lab3/secret.html')