import os
from datetime import datetime

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

ADMIN_ROLE_NAME = 'Администратор'


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role = db.relationship('Role', back_populates='users')

    @property
    def username(self):
        return self.login

    @property
    def full_name(self):
        parts = [self.surname, self.first_name, self.patronymic]
        return ' '.join(p for p in parts if p)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role is not None and self.role.name == ADMIN_ROLE_NAME

    def can_edit(self, target):
        return self.is_admin or self.id == target.id

    def can_delete(self, target):
        return self.is_admin or self.id == target.id

    def get_id(self):
        return f'db_{self.id}'

    def __repr__(self):
        return f'<User {self.login}>'


GUEST_USER_LABEL = 'Неаутентифицированный пользователь'


class VisitLog(db.Model):
    __tablename__ = 'visit_logs'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='visit_logs')

    def display_user_name(self):
        if self.user is not None:
            return self.user.full_name or self.user.login
        return GUEST_USER_LABEL

    def __repr__(self):
        return f'<VisitLog {self.path}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.String(100), primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    md5_hash = db.Column(db.String(100), unique=True, nullable=False)
    object_id = db.Column(db.Integer, nullable=True)
    object_type = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def storage_filename(self):
        _, ext = os.path.splitext(self.file_name)
        return self.id + ext

    @property
    def url(self):
        return url_for('lab6.image', image_id=self.id)

    def __repr__(self):
        return f'<Image {self.file_name}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_desc = db.Column(db.Text, nullable=False)
    full_desc = db.Column(db.Text, nullable=False)
    rating_sum = db.Column(db.Integer, default=0, nullable=False)
    rating_num = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    background_image_id = db.Column(db.String(100), db.ForeignKey('images.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    author = db.relationship('User')
    category = db.relationship('Category', lazy=False)
    bg_image = db.relationship('Image')

    @property
    def rating(self):
        if self.rating_num > 0:
            return self.rating_sum / self.rating_num
        return 0

    def __repr__(self):
        return f'<Course {self.name}>'


RATING_CHOICES = [
    (5, 'отлично'),
    (4, 'хорошо'),
    (3, 'удовлетворительно'),
    (2, 'неудовлетворительно'),
    (1, 'плохо'),
    (0, 'ужасно'),
]

RATING_LABELS = dict(RATING_CHOICES)


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    course = db.relationship('Course', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', backref='reviews')

    def rating_label(self):
        return RATING_LABELS.get(self.rating, str(self.rating))

    def __repr__(self):
        return f'<Review {self.id} course={self.course_id}>'
