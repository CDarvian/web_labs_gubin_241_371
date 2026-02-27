import os
import sys
import pytest

# Принудительно добавляем директорию с app.py в пути поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Импортируем именно файл app.py как модуль (называем его app_module, чтобы не путать с Flask)
import app as app_module

# 1. Проверка корневой страницы хостинга
def test_main_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Мои лабораторные работы" in response.text

# 2. Проверка страницы с заданием
def test_lab1_index(client):
    response = client.get("/lab1/")
    assert response.status_code == 200
    assert "Задание к лабораторной работе" in response.text

# 3. Проверка успешного ответа страницы постов
def test_posts_index_status(client):
    response = client.get("/lab1/posts")
    assert response.status_code == 200
    assert "Последние посты" in response.text

# 4. Проверка правильного шаблона и данных на странице постов
def test_posts_index_template(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
        _ = client.get('/lab1/posts')
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'posts.html'
        assert context['title'] == 'Посты'
        assert len(context['posts']) == 1

# 5. Проверка доступности существующего поста
def test_post_status_200(client, mocker, posts_list):
    mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert response.status_code == 200

# 6. Проверка кода 404 при неверном ID
def test_post_status_404(client, mocker, posts_list):
    mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/999")
    assert response.status_code == 404

# 7. Проверка использования правильного шаблона поста
def test_post_template_used(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
        client.get("/lab1/posts/0")
        assert templates[0][0].name == 'post.html'

# 8. Проверка передачи нужных данных (post) в шаблон
def test_post_context_passed(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
        client.get("/lab1/posts/0")
        context = templates[0][1]
        assert 'post' in context
        assert context['post']['title'] == 'Заголовок поста'

# 9. Проверка рендеринга заголовка
def test_post_title_rendered(client, mocker, posts_list):
    mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "Заголовок поста" in response.text

# 10. Проверка рендеринга имени автора
def test_post_author_rendered(client, mocker, posts_list):
    mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "Иванов Иван Иванович" in response.text

# 11. Проверка формата даты (ДД.ММ.ГГГГ)
def test_post_date_formatted(client, mocker, posts_list):
    mocker.patch.object(app_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "10.03.2025" in response.text

# 12. Проверка отображения изображения
def test_post_image_rendered(client, mocker, posts_list):
    mocker.patch.object