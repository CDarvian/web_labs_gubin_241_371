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
from lab5.routes import PER_PAGE
from models import GUEST_USER_LABEL, User, VisitLog
from rights import INSUFFICIENT_RIGHTS_MESSAGE
from seed import seed_database

RIGHTS_FLASH = INSUFFICIENT_RIGHTS_MESSAGE.encode('utf-8')


def _reset_db():
    db.drop_all()
    db.create_all()
    seed_database()


@pytest.fixture
def lab5_client():
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


def _add_visit(path, user_id=None, created_at=None):
    visit = VisitLog(path=path, user_id=user_id, created_at=created_at or datetime.utcnow())
    db.session.add(visit)
    db.session.commit()
    return visit


def test_before_request_logs_get(lab5_client):
    with app_module.app.app_context():
        before = VisitLog.query.count()
    lab5_client.get('/lab4/')
    with app_module.app.app_context():
        after = VisitLog.query.count()
        assert after > before
        last = VisitLog.query.order_by(VisitLog.id.desc()).first()
        assert last.path == '/lab4/'
        assert last.user_id is None


def test_lab5_index_redirect_anonymous(lab5_client):
    res = lab5_client.get('/lab5/')
    assert res.status_code == 302
    assert '/lab4/login' in res.location


def test_lab5_index_admin_sees_all_logs(lab5_client):
    with app_module.app.app_context():
        admin = User.query.filter_by(login='admin').first()
        user = User.query.filter_by(login='user').first()
        _add_visit('/lab4/', admin.id)
        _add_visit('/lab5/', user.id)
    login(lab5_client)
    res = lab5_client.get('/lab5/')
    html = res.data.decode('utf-8')
    assert res.status_code == 200
    assert 'Журнал посещений' in html
    assert 'Губин' in html
    assert 'Иванов' in html


def test_lab5_index_user_sees_only_own_logs(lab5_client):
    with app_module.app.app_context():
        admin = User.query.filter_by(login='admin').first()
        user = User.query.filter_by(login='user').first()
        _add_visit('/lab4/', admin.id)
        _add_visit('/lab5/', user.id)
        _add_visit('/lab4/users', admin.id)
    login(lab5_client, login='user', password='User1234!')
    res = lab5_client.get('/lab5/')
    html = res.data.decode('utf-8')
    assert 'Иванов' in html
    assert '/lab4/users' not in html
    assert html.count('<td>Иванов') >= 1


def test_lab5_guest_label(lab5_client):
    with app_module.app.app_context():
        _add_visit('/lab1/', None)
    login(lab5_client)
    res = lab5_client.get('/lab5/')
    assert GUEST_USER_LABEL in res.data.decode('utf-8')


def test_lab5_pagination(lab5_client):
    with app_module.app.app_context():
        admin = User.query.filter_by(login='admin').first()
        base = datetime.utcnow()
        for i in range(PER_PAGE + 5):
            _add_visit(f'/page/{i}', admin.id, base + timedelta(seconds=i))
    login(lab5_client)
    res = lab5_client.get('/lab5/')
    html = res.data.decode('utf-8')
    assert html.count('<tr>') == PER_PAGE + 1  # header + rows
    res2 = lab5_client.get('/lab5/?page=2')
    assert res2.status_code == 200
    assert 'page=2' in res2.data.decode('utf-8') or 'active' in res2.data.decode('utf-8')


def test_lab5_admin_report_links(lab5_client):
    login(lab5_client)
    res = lab5_client.get('/lab5/')
    html = res.data.decode('utf-8')
    assert 'Отчёт по страницам' in html
    assert 'Отчёт по пользователям' in html


def test_lab5_user_no_report_links(lab5_client):
    login(lab5_client, login='user', password='User1234!')
    res = lab5_client.get('/lab5/')
    html = res.data.decode('utf-8')
    assert 'Отчёт по страницам' not in html


def test_report_pages_sorted(lab5_client):
    with app_module.app.app_context():
        _add_visit('/report-path-aaa')
        _add_visit('/report-path-aaa')
        _add_visit('/report-path-bbb')
    login(lab5_client)
    res = lab5_client.get('/lab5/reports/pages')
    html = res.data.decode('utf-8')
    pos_a = html.find('/report-path-aaa')
    pos_b = html.find('/report-path-bbb')
    assert pos_a != -1 and pos_b != -1
    assert pos_a < pos_b
    assert '>2</td>' in html


def test_report_users_sorted(lab5_client):
    with app_module.app.app_context():
        admin = User.query.filter_by(login='admin').first()
        user = User.query.filter_by(login='user').first()
        for _ in range(3):
            _add_visit('/x', admin.id)
        _add_visit('/y', user.id)
    login(lab5_client)
    res = lab5_client.get('/lab5/reports/users')
    html = res.data.decode('utf-8')
    assert html.find('Губин') < html.find('Иванов')


def test_user_cannot_access_reports(lab5_client):
    login(lab5_client, login='user', password='User1234!')
    res = lab5_client.get('/lab5/reports/pages', follow_redirects=True)
    assert RIGHTS_FLASH in res.data


def test_export_pages_csv(lab5_client):
    with app_module.app.app_context():
        _add_visit('/test-page')
    login(lab5_client)
    res = lab5_client.get('/lab5/reports/pages.csv')
    assert res.status_code == 200
    assert 'attachment' in res.headers.get('Content-Disposition', '')
    body = res.data.decode('utf-8-sig')
    assert 'Страница' in body
    assert '/test-page' in body


def test_export_users_csv(lab5_client):
    with app_module.app.app_context():
        admin = User.query.filter_by(login='admin').first()
        _add_visit('/z', admin.id)
    login(lab5_client)
    res = lab5_client.get('/lab5/reports/users.csv')
    assert res.status_code == 200
    body = res.data.decode('utf-8-sig')
    assert 'Пользователь' in body
    assert 'Губин' in body
