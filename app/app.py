import random
from functools import lru_cache
from flask import Flask, render_template, Blueprint, abort
from faker import Faker

fake = Faker()

app = Flask(__name__)
application = app

# Создаем Blueprint для первой лабораторной
lab1_bp = Blueprint('lab1', __name__, url_prefix='/lab1')

images_ids = ['7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
              '2d2ab7df-cdbc-48a8-a936-35bba702def5',
              '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
              'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
              'cab5b7f2-774e-4884-a200-0c0180fa777f']


def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = {'author': fake.name(), 'text': fake.text()}
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments


def generate_post(i):
    return {
        'title': 'Заголовок поста',
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }


@lru_cache
def posts_list():
    return sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)


# --- Маршруты лабораторной №1 ---
@lab1_bp.route('/')
def index():
    return render_template('index.html')


@lab1_bp.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list())


@lab1_bp.route('/posts/<int:index>')
def post(index):
    posts = posts_list()
    # Обработка ошибки 404
    if index < 0 or index >= len(posts):
        abort(404)

    p = posts[index]
    return render_template('post.html', title=p['title'], post=p)


@lab1_bp.route('/about')
def about():
    return render_template('about.html', title='Об авторе')


# Регистрируем Blueprint в приложении
app.register_blueprint(lab1_bp)


# --- Главная страница всего репозитория ---
@app.route('/')
def main_index():
    # Эта страница будет оглавлением для всех будущих лаб на хостинге
    return """
    <div style="font-family: sans-serif; padding: 2rem;">
        <h1>Мои лабораторные работы</h1>
        <ul>
            <li><a href="/lab1/">Лабораторная работа №1</a></li>
        </ul>
    </div>
    """