import re

LOGIN_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
PASSWORD_ALLOWED_PATTERN = re.compile(
    r'^[a-zA-Zа-яА-ЯёЁ0-9~!?@#$%^&*_\-+()\[\]{}><\\/|"\'.:,;]+$'
)
UPPERCASE_PATTERN = re.compile(r'[A-ZА-ЯЁ]')
LOWERCASE_PATTERN = re.compile(r'[a-zа-яё]')
DIGIT_PATTERN = re.compile(r'[0-9]')


def validate_login(login):
    errors = {}
    if not login or not login.strip():
        errors['login'] = 'Поле не может быть пустым'
    elif len(login) < 5:
        errors['login'] = 'Логин должен содержать не менее 5 символов'
    elif not LOGIN_PATTERN.match(login):
        errors['login'] = 'Логин должен состоять только из латинских букв и цифр'
    return errors


def validate_password(password):
    errors = {}
    if not password:
        errors['password'] = 'Поле не может быть пустым'
        return errors

    if len(password) < 8:
        errors['password'] = 'Пароль должен содержать не менее 8 символов'
    elif len(password) > 128:
        errors['password'] = 'Пароль должен содержать не более 128 символов'
    elif ' ' in password:
        errors['password'] = 'Пароль не должен содержать пробелы'
    elif not UPPERCASE_PATTERN.search(password):
        errors['password'] = 'Пароль должен содержать хотя бы одну заглавную букву'
    elif not LOWERCASE_PATTERN.search(password):
        errors['password'] = 'Пароль должен содержать хотя бы одну строчную букву'
    elif not DIGIT_PATTERN.search(password):
        errors['password'] = 'Пароль должен содержать хотя бы одну цифру'
    elif not PASSWORD_ALLOWED_PATTERN.match(password):
        errors['password'] = 'Пароль содержит недопустимые символы'

    return errors


def validate_user_fields(surname, first_name, patronymic=None, require_surname=True):
    errors = {}
    if require_surname and (not surname or not surname.strip()):
        errors['surname'] = 'Поле не может быть пустым'
    if not first_name or not first_name.strip():
        errors['first_name'] = 'Поле не может быть пустым'
    return errors


def validate_create_user(form_data):
    errors = {}
    errors.update(validate_login(form_data.get('login', '')))
    errors.update(validate_password(form_data.get('password', '')))
    errors.update(validate_user_fields(
        form_data.get('surname', ''),
        form_data.get('first_name', ''),
        form_data.get('patronymic', ''),
    ))
    return errors


def validate_edit_user(form_data):
    return validate_user_fields(
        form_data.get('surname', ''),
        form_data.get('first_name', ''),
        form_data.get('patronymic', ''),
    )


def validate_change_password(old_password, new_password, confirm_password, user):
    errors = {}
    if not old_password:
        errors['old_password'] = 'Поле не может быть пустым'
    elif not user.check_password(old_password):
        errors['old_password'] = 'Неверный старый пароль'

    new_errors = validate_password(new_password)
    if new_errors:
        errors.update({f'new_password': new_errors['password']})

    if not confirm_password:
        errors['confirm_password'] = 'Поле не может быть пустым'
    elif new_password != confirm_password:
        errors['confirm_password'] = 'Пароли не совпадают'

    return errors
