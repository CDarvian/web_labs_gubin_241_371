import os
import sys
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Теперь мокаем данные прямо из модуля lab1
import lab1 as lab1_module


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
        mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
        _ = client.get('/lab1/posts')
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'posts.html'
        assert context['title'] == 'Посты'
        assert len(context['posts']) == 1


# 5. Проверка доступности существующего поста
def test_post_status_200(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert response.status_code == 200


# 6. Проверка кода 404 при неверном ID
def test_post_status_404(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/999")
    assert response.status_code == 404


# 7. Проверка использования правильного шаблона поста
def test_post_template_used(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
        client.get("/lab1/posts/0")
        assert templates[0][0].name == 'post.html'


# 8. Проверка передачи нужных данных (post) в шаблон
def test_post_context_passed(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
        client.get("/lab1/posts/0")
        context = templates[0][1]
        assert 'post' in context
        assert context['post']['title'] == 'Заголовок поста'


# 9. Проверка рендеринга заголовка
def test_post_title_rendered(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "Заголовок поста" in response.text


# 10. Проверка рендеринга имени автора
def test_post_author_rendered(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "Иванов Иван Иванович" in response.text


# 11. Проверка формата даты (ДД.ММ.ГГГГ)
def test_post_date_formatted(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "10.03.2025" in response.text


# 12. Проверка отображения изображения
def test_post_image_rendered(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "123.jpg" in response.text


# 13. Проверка наличия формы комментариев
def test_post_form_rendered(client, mocker, posts_list):
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)
    response = client.get("/lab1/posts/0")
    assert "Оставьте комментарий" in response.text
    assert "<textarea" in response.text


# 14. Проверка отображения подвала (footer) с ФИО
def test_footer_rendered(client):
    response = client.get("/lab1/")
    assert "<footer" in response.text
    assert "ФИО:" in response.text


# 15. Проверка рендеринга самих комментариев
def test_post_comments_rendered(client, mocker, posts_list):
    posts_list[0]['comments'] = [{'author': 'Петр Петров', 'text': 'Тестовый текст', 'replies': []}]
    mocker.patch.object(lab1_module, 'posts_list', return_value=posts_list, autospec=True)

    response = client.get("/lab1/posts/0")
    assert "Петр Петров" in response.text
    assert "Тестовый текст" in response.text