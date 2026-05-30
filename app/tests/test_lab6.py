import os
import sys
from datetime import datetime, timedelta

import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import app as app_module
from extensions import db
from lab6.courses import REVIEWS_PER_PAGE
from models import Category, Course, Review, User
from seed import seed_database


def _reset_db():
    db.drop_all()
    db.create_all()
    seed_database()


@pytest.fixture
def lab6_client():
    app_module.app.config['TESTING'] = True
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app_module.app.app_context():
        db.engine.dispose()
        _reset_db()
        with app_module.app.test_client() as client:
            yield client
        db.session.remove()


def login(client, login='admin', password='Admin123!'):
    return client.post('/lab4/login', data={'login': login, 'password': password})


def _create_course(name='Тестовый курс'):
    category = Category.query.first()
    author = User.query.filter_by(login='admin').first()
    course = Course(
        name=name,
        short_desc='Краткое описание',
        full_desc='Полное описание',
        category_id=category.id,
        author_id=author.id,
    )
    db.session.add(course)
    db.session.commit()
    return course


def _create_review(course, user, rating, text, created_at=None):
    review = Review(
        course_id=course.id,
        user_id=user.id,
        rating=rating,
        text=text,
        created_at=created_at or datetime.utcnow(),
    )
    course.rating_sum += rating
    course.rating_num += 1
    db.session.add(review)
    db.session.commit()
    return review


def test_show_displays_last_five_reviews(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        users = User.query.all()
        for i in range(7):
            user = users[i % len(users)]
            _create_review(course, user, i % 6, f'Отзыв номер {i + 1}')

    res = lab6_client.get(f'/courses/{course_id}')
    html = res.data.decode('utf-8')
    assert res.status_code == 200
    assert 'Отзыв номер 7' in html
    assert 'Отзыв номер 3' in html
    assert 'Отзыв номер 1' not in html
    assert 'Губин' in html or 'Иванов' in html


def test_show_all_reviews_button(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
    res = lab6_client.get(f'/courses/{course_id}')
    html = res.data.decode('utf-8')
    assert f'/courses/{course_id}/reviews' in html
    assert 'Все отзывы' in html


def test_reviews_pagination(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        users = User.query.all()
        for i in range(REVIEWS_PER_PAGE + 2):
            _create_review(course, users[0], 5, f'Paginated review #{i + 1:02d}')

    res = lab6_client.get(f'/courses/{course_id}/reviews')
    html = res.data.decode('utf-8')
    assert res.status_code == 200
    assert 'Paginated review #12' in html
    assert 'Paginated review #01' not in html
    assert 'Paginated review #02' not in html

    res2 = lab6_client.get(f'/courses/{course_id}/reviews?page=2')
    html2 = res2.data.decode('utf-8')
    assert res2.status_code == 200
    assert 'Paginated review #01' in html2
    assert 'Paginated review #02' in html2


def test_reviews_sort_newest(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        user = User.query.first()
        base = datetime(2024, 1, 1)
        _create_review(course, user, 3, 'Старый отзыв', base)
        _create_review(course, user, 4, 'Новый отзыв', base + timedelta(days=1))

    res = lab6_client.get(f'/courses/{course_id}/reviews?sort=newest')
    html = res.data.decode('utf-8')
    assert html.index('Новый отзыв') < html.index('Старый отзыв')


def test_reviews_sort_positive(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        user = User.query.first()
        _create_review(course, user, 1, 'Низкая оценка')
        _create_review(course, user, 5, 'Высокая оценка')

    res = lab6_client.get(f'/courses/{course_id}/reviews?sort=positive')
    html = res.data.decode('utf-8')
    assert html.index('Высокая оценка') < html.index('Низкая оценка')


def test_reviews_sort_negative(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        user = User.query.first()
        _create_review(course, user, 5, 'Высокая оценка')
        _create_review(course, user, 1, 'Низкая оценка')

    res = lab6_client.get(f'/courses/{course_id}/reviews?sort=negative')
    html = res.data.decode('utf-8')
    assert html.index('Низкая оценка') < html.index('Высокая оценка')


def test_sort_preserved_in_pagination(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id
        user = User.query.first()
        for i in range(REVIEWS_PER_PAGE + 1):
            _create_review(course, user, i % 6, f'Review {i + 1}')

    res = lab6_client.get(f'/courses/{course_id}/reviews?sort=positive')
    html = res.data.decode('utf-8')
    assert 'sort=positive' in html


def test_create_review_updates_course_rating(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id

    login(lab6_client, login='user', password='User1234!')
    res = lab6_client.post(
        f'/courses/{course_id}/reviews',
        data={'rating': 4, 'text': 'Хороший курс'},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app_module.app.app_context():
        course = db.session.get(Course, course_id)
        assert course.rating_sum == 4
        assert course.rating_num == 1
        review = Review.query.filter_by(course_id=course_id).first()
        assert review.text == 'Хороший курс'
        assert review.rating == 4


def test_create_review_requires_login(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        course_id = course.id

    res = lab6_client.post(
        f'/courses/{course_id}/reviews',
        data={'rating': 5, 'text': 'Отзыв без входа'},
    )
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_existing_review_hides_form(lab6_client):
    with app_module.app.app_context():
        course = _create_course()
        user = User.query.filter_by(login='user').first()
        _create_review(course, user, 3, 'Мой существующий отзыв')
        course_id = course.id

    login(lab6_client, login='user', password='User1234!')
    res = lab6_client.get(f'/courses/{course_id}')
    html = res.data.decode('utf-8')
    assert res.status_code == 200
    assert 'Мой существующий отзыв' in html
    assert 'Ваш отзыв' in html
    assert 'name="rating"' not in html

    res2 = lab6_client.get(f'/courses/{course_id}/reviews')
    html2 = res2.data.decode('utf-8')
    assert 'Мой существующий отзыв' in html2
    assert 'name="rating"' not in html2
