"""Хранилище конфигов."""
import logging
import os
from typing import Dict
from urllib import parse
from fastapi import WebSocket


class ConfigError(KeyError):
    """Ошибка конфигурации."""


class ConfigAbstract:
    """Класс конфигурации переменных окружения."""

    @classmethod
    def ensure_configured(cls) -> None:
        """Метод для проверки переменных конкретной конфигурации."""
        attributes = cls.__dict__
        collected = {name: getattr(cls, name) for name in attributes if not callable(getattr(cls, name))}
        for name, v in collected.items():
            name: str
            if v is None and not name.startswith("_"):
                msg = f"Variable {name} not found for config {cls.__name__}"
                raise ConfigError(msg)


try:

    class AppSettings(ConfigAbstract):
        """Настройки отвечающие за бизнес логику."""

        test_token = os.environ.get("TEST_TOKEN", None)

        token_alive_hours = int(os.environ.get("TOKEN_ALIVE_HOURS", 4))
        refresh_token_alive_hours = int(os.environ.get("REFRESH_TOKEN_ALIVE_HOURS", 24 * 7))

        # переменные для сброса пароля
        reset_password_alive_hours = os.environ.get("RESET_PASSWORD_ALIVE_HOURS", 2)
        reset_password_redirect_page = os.environ.get("RESET_PASSWORD_REDIRECT_PAGE")


    class AppConfig(ConfigAbstract):
        """Обязательные для конфигурирования настройки при запуске."""

        host = os.environ.get("HOST", "localhost")
        port = int(os.environ.get("PORT", 7001))
        portal_address = os.environ.get("PORTAL_ADDRESS")  # публичный адрес сервиса для генерации ссылок

        debug_mode = os.environ.get("DEBUG_MODE", "").lower() == "true"

        cors_policy_disabled = os.environ.get("CORS_POLICY_DISABLED", "True").lower() == "true"
        secret = os.environ.get("SECRET", "Pepa the pig")
        algorithm = "SHA256"
        # директория для хранения прикрепляемых файлов
        file_directory = os.environ.get("FILE_DIRECTORY", None)

        log_level = getattr(logging, os.environ.get("LOG_LEVEL", "DEBUG"))
        additional_debug = os.environ.get("ADDITIONAL_DEBUG", "False").lower() == "true"

        active_connections: Dict[int, WebSocket] = {}


    class DBConfig(ConfigAbstract):
        """Параметры для подключения к БД."""

        db_name = os.environ["DB_NAME"]
        db_password = os.environ["DB_PASSWORD"]
        db_host = os.environ["DB_HOST"]
        db_port = os.environ["DB_PORT"]
        db_user = os.environ["DB_USER"]

        db_conn_str = f"postgresql://{db_user}:{parse.quote(db_password)}@{db_host}:{db_port}/{db_name}"
        async_db_conn_str = f"postgresql+asyncpg://{db_user}:{parse.quote(db_password)}@{db_host}:{db_port}/{db_name}"


    class NotificationServiceConfig(ConfigAbstract):
        """Конфигурация для сервиса уведомлений."""

        notification_service_url = os.environ.get("NOTIFICATION_SERVICE_URL")
        notification_service_token = os.environ.get("NOTIFICATION_SERVICE_TOKEN")


    class Auth(ConfigAbstract):
        SECRET_KEY = os.environ.get("SECRET")
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30


    class Config(  # noqa: D101
        AppSettings,
        AppConfig,
        DBConfig,
        Auth,

    ):
        pass

except KeyError as e:
    msg = f"Unable to found environment variable {e!s}"
    raise ConfigError(msg) from e
