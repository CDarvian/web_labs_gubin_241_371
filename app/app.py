from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
import os

from extensions import db

app = Flask(__name__)
application = app
app.config['SECRET_KEY'] = 'super_secret_key_for_flask_app'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lab4.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'media', 'images')

db.init_app(app)
migrate = Migrate(app, db)

# --- Инициализация Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'lab4.login'
login_manager.login_message = 'Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'warning'

# --- Подключение всех лабораторных (Blueprints) ---
from lab1 import lab1_bp
app.register_blueprint(lab1_bp)

from lab2 import lab2_bp
app.register_blueprint(lab2_bp)

from lab3 import lab3_bp, users_db
app.register_blueprint(lab3_bp)

from lab4 import lab4_bp
app.register_blueprint(lab4_bp)

from lab5 import lab5_bp
app.register_blueprint(lab5_bp)

from lab6 import courses_bp, lab6_bp
app.register_blueprint(courses_bp)
app.register_blueprint(lab6_bp)

from models import User
from seed import seed_database
from visit_logging import register_visit_logging

register_visit_logging(app)


@login_manager.user_loader
def load_user(user_id):
    if isinstance(user_id, str) and user_id.startswith('db_'):
        try:
            return db.session.get(User, int(user_id[3:]))
        except (TypeError, ValueError):
            pass
    for user in users_db.values():
        if str(user.id) == str(user_id):
            return user
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash(login_manager.login_message, login_manager.login_message_category)
    if request.path.startswith('/lab3'):
        return redirect(url_for('lab3.login', next=request.url))
    return redirect(url_for('lab4.login', next=request.url))


with app.app_context():
    seed_database()


# --- Главная страница всего репозитория ---
@app.route('/')
def main_index():
    return """
    <div style="font-family: sans-serif; padding: 2rem;">
        <h1>Мои лабораторные работы</h1>
        <ul>
            <li><a href="/lab1/">Лабораторная работа №1</a></li>
            <li><a href="/lab2/">Лабораторная работа №2</a></li>
            <li><a href="/lab3/">Лабораторная работа №3</a></li>
            <li><a href="/lab4/">Лабораторная работа №4</a></li>
            <li><a href="/lab5/">Лабораторная работа №5</a></li>
            <li><a href="/courses/">Лабораторная работа №6</a></li>
        </ul>
    </div>
    """

if __name__ == '__main__':
    app.run(debug=True)
