from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from extensions import db
from lab6.repositories import (
    CategoryRepository,
    CourseRepository,
    ImageRepository,
    ReviewRepository,
    UserRepository,
)
from lab6.repositories.review_repository import SORT_NEWEST, VALID_SORTS
from models import RATING_CHOICES

user_repository = UserRepository(db)
course_repository = CourseRepository(db)
category_repository = CategoryRepository(db)
image_repository = ImageRepository(db)
review_repository = ReviewRepository(db)

courses_bp = Blueprint(
    'courses',
    __name__,
    url_prefix='/courses',
    template_folder='../templates/lab6',
)

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc',
]

REVIEWS_PER_PAGE = 10


def _params():
    return {p: request.form.get(p) or None for p in COURSE_PARAMS}


def _search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }


def _sort_param():
    sort = request.args.get('sort', SORT_NEWEST)
    return sort if sort in VALID_SORTS else SORT_NEWEST


def _review_context(course):
    user_review = None
    if current_user.is_authenticated:
        user_review = review_repository.get_user_review(course.id, current_user.id)
    return {
        'user_review': user_review,
        'rating_choices': RATING_CHOICES,
    }


@courses_bp.route('/')
def index():
    pagination = course_repository.get_pagination_info(**_search_params())
    courses = course_repository.get_all_courses(pagination=pagination)
    categories = category_repository.get_all_categories()
    return render_template(
        'courses/index.html',
        courses=courses,
        categories=categories,
        pagination=pagination,
        search_params=_search_params(),
    )


@courses_bp.route('/new')
@login_required
def new():
    course = course_repository.new_course()
    categories = category_repository.get_all_categories()
    users = user_repository.get_all_users()
    return render_template(
        'courses/new.html',
        categories=categories,
        users=users,
        course=course,
    )


@courses_bp.route('/create', methods=['POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = None

    try:
        if f and f.filename:
            img = image_repository.add_image(f)

        image_id = img.id if img else None
        course = course_repository.add_course(**_params(), background_image_id=image_id)
    except IntegrityError as err:
        flash(
            f'Возникла ошибка при записи данных в БД. '
            f'Проверьте корректность введённых данных. ({err})',
            'danger',
        )
        categories = category_repository.get_all_categories()
        users = user_repository.get_all_users()
        return render_template(
            'courses/new.html',
            categories=categories,
            users=users,
            course=course,
        )

    flash(f'Курс {course.name} был успешно добавлен!', 'success')
    return redirect(url_for('courses.index'))


@courses_bp.route('/<int:course_id>')
def show(course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        abort(404)
    reviews = review_repository.get_latest(course_id)
    return render_template(
        'courses/show.html',
        course=course,
        reviews=reviews,
        **_review_context(course),
    )


@courses_bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        abort(404)
    sort = _sort_param()
    pagination = review_repository.get_paginated(
        course_id,
        sort=sort,
        page=request.args.get('page', 1, type=int),
        per_page=REVIEWS_PER_PAGE,
    )
    return render_template(
        'courses/reviews.html',
        course=course,
        reviews=pagination.items,
        pagination=pagination,
        sort=sort,
        sort_params={'sort': sort, 'course_id': course.id},
        **_review_context(course),
    )


@courses_bp.route('/<int:course_id>/reviews', methods=['POST'])
@login_required
def create_review(course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        abort(404)

    if review_repository.get_user_review(course_id, current_user.id):
        flash('Вы уже оставили отзыв на этот курс.', 'warning')
        return redirect(request.referrer or url_for('courses.show', course_id=course_id))

    rating = request.form.get('rating', type=int)
    text = (request.form.get('text') or '').strip()

    if rating is None or text == '':
        flash('Заполните все поля отзыва.', 'danger')
        return redirect(request.referrer or url_for('courses.show', course_id=course_id))

    review_repository.add_review(course, current_user.id, rating, text)
    flash('Отзыв успешно добавлен.', 'success')

    sort = request.form.get('sort') or _sort_param()
    referrer = request.referrer or ''
    if f'/courses/{course_id}/reviews' in referrer:
        return redirect(url_for('courses.reviews', course_id=course_id, sort=sort))
    return redirect(url_for('courses.show', course_id=course_id))
