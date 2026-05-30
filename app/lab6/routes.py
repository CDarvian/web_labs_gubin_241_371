from flask import Blueprint, abort, current_app, redirect, send_from_directory, url_for

from extensions import db
from lab6.repositories import ImageRepository

image_repository = ImageRepository(db)

lab6_bp = Blueprint(
    'lab6',
    __name__,
    url_prefix='/lab6',
    template_folder='../templates/lab6',
    static_folder='../static/lab6',
    static_url_path='/static/lab6',
)


@lab6_bp.route('/')
def index():
    return redirect(url_for('courses.index'))


@lab6_bp.route('/images/<image_id>')
def image(image_id):
    img = image_repository.get_by_id(image_id)
    if img is None:
        abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], img.storage_filename)
