# app/tests/test_lab2.py

# 1. Тест параметров URL
def test_url_params(client):
    response = client.get('/lab2/url?testparam=helloworld')
    assert "testparam" in response.data.decode('utf-8')
    assert "helloworld" in response.data.decode('utf-8')

# 2. Тест заголовков запроса
def test_headers_display(client):
    response = client.get('/lab2/headers', headers={'X-Test-Header': 'SecretValue'})
    assert "X-Test-Header" in response.data.decode('utf-8')
    assert "SecretValue" in response.data.decode('utf-8')

# 3. Тест установки Cookie
def test_cookie_set(client):
    response = client.get('/lab2/cookies')
    assert 'lab2_cookie=im_a_cookie_value' in response.headers.getlist('Set-Cookie')[0]

# 4. Тест удаления Cookie
def test_cookie_delete(client):
    # Убрали 'localhost', оставляем только ключ и значение
    client.set_cookie('lab2_cookie', 'some_value')
    response = client.get('/lab2/cookies')
    # Проверяем, что в Set-Cookie передано указание удалить куки (Expires=Thu, 01 Jan 1970)
    assert 'Expires=Thu, 01 Jan 1970' in response.headers.getlist('Set-Cookie')[0]

# 5. Тест GET-запроса формы параметров
def test_form_params_get(client):
    response = client.get('/lab2/form')
    assert "Данные из POST-запроса:" not in response.data.decode('utf-8')

# 6. Тест POST-запроса формы параметров
def test_form_params_post(client):
    response = client.post('/lab2/form', data={'secret_field': '42'})
    assert "secret_field" in response.data.decode('utf-8')
    assert "42" in response.data.decode('utf-8')

# 7. Валидация: правильный номер 10 цифр (без +7 или 8)
def test_phone_valid_10_digits(client):
    response = client.post('/lab2/phone', data={'phone': '123.456.75.90'})
    assert "8-123-456-75-90" in response.data.decode('utf-8')

# 8. Валидация: правильный номер 11 цифр (начинается с +7)
def test_phone_valid_11_digits_plus7(client):
    response = client.post('/lab2/phone', data={'phone': '+7 (123) 456-75-90'})
    assert "8-123-456-75-90" in response.data.decode('utf-8')

# 9. Валидация: правильный номер 11 цифр (начинается с 8)
def test_phone_valid_11_digits_8(client):
    response = client.post('/lab2/phone', data={'phone': '8(123)4567590'})
    assert "8-123-456-75-90" in response.data.decode('utf-8')

# 10. Ошибка: недопустимые символы (буквы)
def test_phone_invalid_chars_letters(client):
    response = client.post('/lab2/phone', data={'phone': '+7 999 abc 44 55'})
    assert "В номере телефона встречаются недопустимые символы" in response.data.decode('utf-8')

# 11. Ошибка: недопустимые символы (спецсимволы)
def test_phone_invalid_chars_symbols(client):
    response = client.post('/lab2/phone', data={'phone': '8!123!4567590'})
    assert "В номере телефона встречаются недопустимые символы" in response.data.decode('utf-8')

# 12. Ошибка: слишком мало цифр (9 цифр вместо 10)
def test_phone_invalid_length_too_short(client):
    response = client.post('/lab2/phone', data={'phone': '123 456 75 9'})
    assert "Неверное количество цифр" in response.data.decode('utf-8')

# 13. Ошибка: слишком много цифр (12 цифр)
def test_phone_invalid_length_too_long(client):
    response = client.post('/lab2/phone', data={'phone': '8 (123) 456-75-900'})
    assert "Неверное количество цифр" in response.data.decode('utf-8')

# 14. Ошибка: начинается с +7, но всего 10 цифр
def test_phone_invalid_length_plus7_short(client):
    response = client.post('/lab2/phone', data={'phone': '+7 (12) 456-75-90'})
    assert "Неверное количество цифр" in response.data.decode('utf-8')

# 15. Проверка классов Bootstrap при ошибке
def test_phone_error_bootstrap_classes(client):
    response = client.post('/lab2/phone', data={'phone': 'wrong_number'})
    html = response.data.decode('utf-8')
    assert "is-invalid" in html
    assert "invalid-feedback" in html