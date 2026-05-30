from flask import Blueprint

lab5_bp = Blueprint('lab5', __name__, url_prefix='/lab5')

from lab5 import reports, routes  # noqa: E402, F401
