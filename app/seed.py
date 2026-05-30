from sqlalchemy.exc import OperationalError

from extensions import db
from models import ADMIN_ROLE_NAME, Category, Role, User


def seed_database():
    try:
        if Role.query.first() is not None:
            _seed_categories()
            return
    except OperationalError:
        db.session.rollback()
        return

    admin_role = Role(name=ADMIN_ROLE_NAME, description='Полный доступ к системе')
    user_role = Role(name='Пользователь', description='Обычный пользователь')
    db.session.add_all([admin_role, user_role])
    db.session.flush()

    admin = User(
        login='admin',
        surname='Губин',
        first_name='Даниил',
        patronymic='Павлович',
        role_id=admin_role.id,
    )
    admin.set_password('Admin123!')
    db.session.add(admin)

    regular = User(
        login='user',
        surname='Иванов',
        first_name='Иван',
        patronymic='Иванович',
        role_id=user_role.id,
    )
    regular.set_password('User1234!')
    db.session.add(regular)
    db.session.commit()
    _seed_categories()


def _seed_categories():
    try:
        if Category.query.first() is not None:
            return
    except OperationalError:
        db.session.rollback()
        return
    categories = [
        Category(name='Программирование'),
        Category(name='Математика'),
        Category(name='Физика'),
    ]
    db.session.add_all(categories)
    db.session.commit()
