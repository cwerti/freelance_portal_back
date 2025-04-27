from passlib.handlers.pbkdf2 import pbkdf2_sha512


def generate_password_hash(password: str) -> str:
    """
    Создаёт хэш пароля для хранения в БД
    """
    return pbkdf2_sha512.hash(password)


def verify_password(input_password: str, password_hash: str) -> bool:
    """
    Сравнивает полученный вариант пароля с захэшированным вариантом
    """
    return pbkdf2_sha512.verify(input_password, password_hash)
