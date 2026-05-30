import os
import sys

import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import app as app_module
from extensions import db
from models import Role, User
from rights import INSUFFICIENT_RIGHTS_MESSAGE
from seed import seed_database

RIGHTS_FLASH = INSUFFICIENT_RIGHTS_MESSAGE.encode('utf-8')


def _reset_db():
    db.drop_all()
    db.create_all()
    seed_database()


@pytest.fixture
def lab4_client():
    app_module.app.config['TESTING'] = True
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app_module.app.app_context():
        db.engine.dispose()
        _reset_db()
    with app_module.app.test_client() as client:
        with app_module.app.app_context():
            yield client
        db.session.remove()


def login(client, login='admin', password='Admin123!'):
    return client.post('/lab4/login', data={'login': login, 'password': password})


# --- Index ---

def test_index_accessible_anonymous(lab4_client):
    res = lab4_client.get('/lab4/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert 'Список пользователей' in html
    assert 'Губин' in html


def test_index_hides_auth_buttons_anonymous(lab4_client):
    res = lab4_client.get('/lab4/')
    html = res.data.decode('utf-8')
    assert 'Создание пользователя' not in html
    assert 'Редактирование' not in html
    assert 'data-bs-target="#deleteModal' not in html


def test_index_shows_auth_buttons(lab4_client):
    login(lab4_client)
    res = lab4_client.get('/lab4/')
    html = res.data.decode('utf-8')
    assert 'Создание пользователя' in html
    assert 'Редактирование' in html
    assert 'data-bs-target="#deleteModal' in html


def test_index_row_number(lab4_client):
    res = lab4_client.get('/lab4/')
    html = res.data.decode('utf-8')
    assert '<td>1</td>' in html


# --- View ---

def test_view_user_anonymous(lab4_client):
    with app_module.app.app_context():
        user = User.query.filter_by(login='admin').first()
        user_id = user.id
    res = lab4_client.get(f'/lab4/users/{user_id}')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_view_user_not_found(lab4_client):
    login(lab4_client)
    res = lab4_client.get('/lab4/users/9999', follow_redirects=True)
    assert 'Пользователь не найден'.encode('utf-8') in res.data


def test_regular_user_can_view_own_profile(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='user').first().id
    res = lab4_client.get(f'/lab4/users/{user_id}')
    assert res.status_code == 200
    assert 'Иванов' in res.data.decode('utf-8')


def test_regular_user_cannot_view_other_profile(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        admin_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.get(f'/lab4/users/{admin_id}', follow_redirects=True)
    assert RIGHTS_FLASH in res.data


# --- Create ---

def test_create_redirect_anonymous(lab4_client):
    res = lab4_client.get('/lab4/users/create')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_create_success(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user_role = Role.query.filter_by(name='Пользователь').first()
        role_id = user_role.id
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'newuser',
        'password': 'Newpass1',
        'surname': 'Иванов',
        'first_name': 'Иван',
        'patronymic': 'Иванович',
        'role_id': str(role_id),
    }, follow_redirects=True)
    assert 'Пользователь успешно создан'.encode('utf-8') in res.data
    with app_module.app.app_context():
        user = User.query.filter_by(login='newuser').first()
        assert user is not None
        assert user.first_name == 'Иван'


def test_create_validation_errors(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'ab',
        'password': 'short',
        'surname': '',
        'first_name': '',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'is-invalid' in html
    assert 'invalid-feedback' in html
    assert 'Логин должен содержать не менее 5 символов' in html


def test_regular_user_cannot_create_user(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    res = lab4_client.get('/lab4/users/create', follow_redirects=True)
    assert RIGHTS_FLASH in res.data
    res = lab4_client.get('/lab4/')
    assert 'Создание пользователя' not in res.data.decode('utf-8')


def test_create_duplicate_login(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'admin',
        'password': 'Newpass1',
        'surname': 'Test',
        'first_name': 'Test',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'уже существует' in html


# --- Edit ---

def test_edit_redirect_anonymous(lab4_client):
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.get(f'/lab4/users/{user_id}/edit')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_edit_prefilled(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.get(f'/lab4/users/{user_id}/edit')
    html = res.data.decode('utf-8')
    assert 'value="Губин"' in html
    assert 'name="login"' not in html
    assert 'name="password"' not in html


def test_edit_success(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user = User.query.filter_by(login='admin').first()
        user_id = user.id
    res = lab4_client.post(f'/lab4/users/{user_id}/edit', data={
        'surname': 'Петров',
        'first_name': 'Пётр',
        'patronymic': 'Петрович',
        'role_id': '',
    }, follow_redirects=True)
    assert 'успешно обновлены'.encode('utf-8') in res.data
    with app_module.app.app_context():
        user = db.session.get(User, user_id)
        assert user.surname == 'Петров'


def test_edit_validation_empty_first_name(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.post(f'/lab4/users/{user_id}/edit', data={
        'surname': 'Test',
        'first_name': '',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'is-invalid' in html
    assert 'Поле не может быть пустым' in html


def test_regular_user_can_edit_self(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='user').first().id
    res = lab4_client.post(f'/lab4/users/{user_id}/edit', data={
        'surname': 'Сидоров',
        'first_name': 'Сидор',
        'patronymic': 'Сидорович',
    }, follow_redirects=True)
    assert 'успешно обновлены'.encode('utf-8') in res.data
    with app_module.app.app_context():
        user = db.session.get(User, user_id)
        assert user.surname == 'Сидоров'


def test_regular_user_cannot_edit_others(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        admin_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.get(f'/lab4/users/{admin_id}/edit', follow_redirects=True)
    assert RIGHTS_FLASH in res.data


def test_regular_user_sees_edit_only_for_self(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    res = lab4_client.get('/lab4/')
    html = res.data.decode('utf-8')
    assert html.count('Редактирование') == 1
    assert html.count('Просмотр') == 1
    assert 'data-bs-target="#deleteModal' not in html
    assert 'Создание пользователя' not in html


def test_regular_user_edit_role_disabled(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='user').first().id
    res = lab4_client.get(f'/lab4/users/{user_id}/edit')
    html = res.data.decode('utf-8')
    assert 'id="role_id"' in html
    assert 'disabled' in html


def test_regular_user_cannot_change_own_role(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        user = User.query.filter_by(login='user').first()
        user_id = user.id
        admin_role_id = Role.query.filter_by(name='Администратор').first().id
        original_role_id = user.role_id
    res = lab4_client.post(f'/lab4/users/{user_id}/edit', data={
        'surname': user.surname,
        'first_name': user.first_name,
        'patronymic': user.patronymic or '',
        'role_id': str(admin_role_id),
    }, follow_redirects=True)
    assert 'успешно обновлены'.encode('utf-8') in res.data
    with app_module.app.app_context():
        user = db.session.get(User, user_id)
        assert user.role_id == original_role_id


def test_admin_can_edit_any_user(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='user').first().id
    res = lab4_client.post(f'/lab4/users/{user_id}/edit', data={
        'surname': 'Петров',
        'first_name': 'Пётр',
        'patronymic': '',
        'role_id': '',
    }, follow_redirects=True)
    assert 'успешно обновлены'.encode('utf-8') in res.data


# --- Delete ---

def test_delete_redirect_anonymous(lab4_client):
    with app_module.app.app_context():
        user = User(login='todelete', first_name='Del', surname='User')
        user.set_password('Delete1!')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    res = lab4_client.post(f'/lab4/users/{user_id}/delete')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_delete_success(lab4_client):
    login(lab4_client)
    with app_module.app.app_context():
        user = User(login='todelete', first_name='Del', surname='User')
        user.set_password('Delete1!')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    res = lab4_client.post(f'/lab4/users/{user_id}/delete', follow_redirects=True)
    assert 'успешно удалён'.encode('utf-8') in res.data
    with app_module.app.app_context():
        assert db.session.get(User, user_id) is None


def test_regular_user_cannot_delete_others(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        admin_id = User.query.filter_by(login='admin').first().id
    res = lab4_client.post(f'/lab4/users/{admin_id}/delete', follow_redirects=True)
    assert RIGHTS_FLASH in res.data
    with app_module.app.app_context():
        assert db.session.get(User, admin_id) is not None


def test_regular_user_cannot_delete_self(lab4_client):
    login(lab4_client, login='user', password='User1234!')
    with app_module.app.app_context():
        user_id = User.query.filter_by(login='user').first().id
    res = lab4_client.post(f'/lab4/users/{user_id}/delete', follow_redirects=True)
    assert RIGHTS_FLASH in res.data
    with app_module.app.app_context():
        assert db.session.get(User, user_id) is not None


# --- Login / Logout ---

def test_login_success(lab4_client):
    res = lab4_client.post('/lab4/login', data={'login': 'admin', 'password': 'Admin123!'})
    assert res.status_code == 302
    assert '/lab4/' in res.location


def test_login_success_message(lab4_client):
    res = lab4_client.post('/lab4/login', data={'login': 'admin', 'password': 'Admin123!'}, follow_redirects=True)
    assert 'Успешный вход!'.encode('utf-8') in res.data


def test_login_fail(lab4_client):
    res = lab4_client.post('/lab4/login', data={'login': 'admin', 'password': 'wrong'}, follow_redirects=True)
    assert 'Неверный логин или пароль'.encode('utf-8') in res.data


def test_remember_me_cookie(lab4_client):
    res = lab4_client.post('/lab4/login', data={
        'login': 'admin', 'password': 'Admin123!', 'remember': 'on',
    })
    assert 'remember_token' in str(res.headers.getlist('Set-Cookie'))


def test_logout(lab4_client):
    login(lab4_client)
    res = lab4_client.get('/lab4/logout', follow_redirects=True)
    html = res.data.decode('utf-8')
    assert 'Войти' in html
    assert 'Выйти' not in html


# --- Change password ---

def test_change_password_redirect_anonymous(lab4_client):
    res = lab4_client.get('/lab4/change-password')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_change_password_wrong_old(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/change-password', data={
        'old_password': 'wrong',
        'new_password': 'Newpass1',
        'confirm_password': 'Newpass1',
    })
    html = res.data.decode('utf-8')
    assert 'Неверный старый пароль' in html


def test_change_password_mismatch(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/change-password', data={
        'old_password': 'Admin123!',
        'new_password': 'Newpass1',
        'confirm_password': 'Otherpass1',
    })
    html = res.data.decode('utf-8')
    assert 'Пароли не совпадают' in html


def test_change_password_weak(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/change-password', data={
        'old_password': 'Admin123!',
        'new_password': 'weak',
        'confirm_password': 'weak',
    })
    html = res.data.decode('utf-8')
    assert 'is-invalid' in html


def test_change_password_success(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/change-password', data={
        'old_password': 'Admin123!',
        'new_password': 'Newpass1',
        'confirm_password': 'Newpass1',
    }, follow_redirects=True)
    assert 'Пароль успешно изменён'.encode('utf-8') in res.data
    lab4_client.get('/lab4/logout')
    res = lab4_client.post('/lab4/login', data={'login': 'admin', 'password': 'Newpass1'})
    assert res.status_code == 302


# --- Validation edge cases ---

def test_login_validation_special_chars(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'user@!',
        'password': 'Validpass1',
        'surname': 'Test',
        'first_name': 'Test',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'латинских букв и цифр' in html


def test_password_validation_no_uppercase(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'validuser',
        'password': 'lowercase1',
        'surname': 'Test',
        'first_name': 'Test',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'заглавную букву' in html


def test_password_validation_space(lab4_client):
    login(lab4_client)
    res = lab4_client.post('/lab4/users/create', data={
        'login': 'validuser',
        'password': 'Valid pass1',
        'surname': 'Test',
        'first_name': 'Test',
        'patronymic': '',
        'role_id': '',
    })
    html = res.data.decode('utf-8')
    assert 'пробелы' in html
