import re
from flask import Blueprint, render_template, request, make_response

# Создаем Blueprint для второй лабы
lab2_bp = Blueprint('lab2', __name__, url_prefix='/lab2')


@lab2_bp.route('/')
def index():
    return render_template('lab2/index.html')


@lab2_bp.route('/url')
def url_params():
    return render_template('lab2/url_params.html', args=request.args)


@lab2_bp.route('/headers')
def headers():
    return render_template('lab2/headers.html', headers=request.headers)


@lab2_bp.route('/cookies')
def cookies():
    # Готовим ответ, чтобы управлять куками
    resp = make_response(render_template('lab2/cookies.html', cookies=request.cookies))

    # Логика из условия: удаляем, если есть, устанавливаем, если нет
    if 'lab2_cookie' in request.cookies:
        resp.delete_cookie('lab2_cookie')
    else:
        resp.set_cookie('lab2_cookie', 'im_a_cookie_value')

    return resp


@lab2_bp.route('/form', methods=['GET', 'POST'])
def form_params():
    form_data = request.form if request.method == 'POST' else None
    return render_template('lab2/form_params.html', form=form_data)


@lab2_bp.route('/phone', methods=['GET', 'POST'])
def phone():
    error = None
    formatted_phone = None
    raw_phone = ""

    if request.method == 'POST':
        raw_phone = request.form.get('phone', '')

        # 1. Проверка на недопустимые символы (только цифры, пробел, (), -, ., +)
        if re.search(r'[^0-9\s\(\)\-\.\+]', raw_phone):
            error = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
        else:
            # Оставляем только цифры для подсчета длины
            digits = re.sub(r'\D', '', raw_phone)
            clean_start = raw_phone.strip()

            # Определяем требуемую длину (11 если начинается с +7 или 8, иначе 10)
            if clean_start.startswith('+7') or clean_start.startswith('8'):
                required_len = 11
            else:
                required_len = 10

            # 2. Проверка количества цифр
            if len(digits) != required_len:
                error = "Недопустимый ввод. Неверное количество цифр."
            else:
                # 3. Форматирование к виду 8-***-***-**-**
                if required_len == 11:
                    formatted_phone = f"8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
                else:
                    formatted_phone = f"8-{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}"

    return render_template('lab2/phone.html', error=error, formatted_phone=formatted_phone, raw_phone=raw_phone)