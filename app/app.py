from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
application = app
app.config['SECRET_KEY'] = 'super_secret_key_for_flask_app'

# --- Инициализация Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'lab3.login'
login_manager.login_message = 'Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'warning'

# --- Подключение всех лабораторных (Blueprints) ---
from lab1 import lab1_bp
app.register_blueprint(lab1_bp)

from lab2 import lab2_bp
app.register_blueprint(lab2_bp)

from lab3 import lab3_bp, users_db
app.register_blueprint(lab3_bp)

@login_manager.user_loader
def load_user(user_id):
    for user in users_db.values():
        if user.id == user_id:
            return user
    return None

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
        </ul>
    </div>
    """

if __name__ == '__main__':
    app.run(debug=True)