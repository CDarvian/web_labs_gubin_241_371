import os
import sys
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import app as app_module

@pytest.fixture
def client():
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client

# 1-2. Счётчик посещений
def test_counter_1(client):
    res = client.get('/lab3/counter')
    assert b'1' in res.data

def test_counter_2(client):
    client.get('/lab3/counter')
    res = client.get('/lab3/counter')
    assert b'2' in res.data

# 3. После успешной аутентификации редирект на главную
def test_auth_success_redirect(client):
    res = client.post('/lab3/login', data={'username': 'user', 'password': 'qwerty'})
    assert res.status_code == 302
    assert '/lab3/' in res.location

# 4. Сообщение об успешном входе
def test_auth_success_message(client):
    res = client.post('/lab3/login', data={'username': 'user', 'password': 'qwerty'}, follow_redirects=True)
    assert 'Успешный вход!'.encode('utf-8') in res.data

# 5. При ошибке остаемся на странице и видим сообщение
def test_auth_fail(client):
    res = client.post('/lab3/login', data={'username': 'user', 'password': 'wrong'}, follow_redirects=True)
    assert 'Неверный логин или пароль.'.encode('utf-8') in res.data
    assert 'Войти'.encode('utf-8') in res.data

# 6. Доступ к секретной странице авторизованным
def test_secret_page_auth(client):
    client.post('/lab3/login', data={'username': 'user', 'password': 'qwerty'})
    res = client.get('/lab3/secret')
    assert res.status_code == 200
    assert 'Секретная страница'.encode('utf-8') in res.data

# 7. Анонимам редирект на логин
def test_secret_page_unauth_redirect(client):
    res = client.get('/lab3/secret')
    assert res.status_code == 302
    assert '/lab3/login' in res.location

# 8. Сообщение анонимам при редиректе
def test_secret_page_unauth_message(client):
    res = client.get('/lab3/secret', follow_redirects=True)
    assert 'необходимо пройти процедуру аутентификации'.encode('utf-8') in res.data

# 9. Возврат на нужную страницу после логина (параметр next)
def test_auth_redirects_next(client):
    res = client.post('/lab3/login?next=/lab3/secret', data={'username': 'user', 'password': 'qwerty'})
    assert res.status_code == 302
    assert '/lab3/secret' in res.location

# 10. Параметр "Запомнить меня" генерирует куки
def test_remember_me_cookie(client):
    res = client.post('/lab3/login', data={'username': 'user', 'password': 'qwerty', 'remember': 'on'})
    assert 'remember_token' in str(res.headers.getlist('Set-Cookie'))

# 11-12. Корректный навбар (скрытие/показ)
def test_navbar_unauth(client):
    res = client.get('/lab3/')
    # Ищем именно HTML-ссылку на секретную страницу, её быть не должно
    assert 'href="/lab3/secret"'.encode('utf-8') not in res.data
    assert 'Войти'.encode('utf-8') in res.data

def test_navbar_auth(client):
    client.post('/lab3/login', data={'username': 'user', 'password': 'qwerty'})
    res = client.get('/lab3/')
    assert 'Секретная страница'.encode('utf-8') in res.data
    assert 'Выйти'.encode('utf-8') in res.data