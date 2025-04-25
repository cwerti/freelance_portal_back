import logging
import traceback
from urllib.request import Request

import fastapi as fastapi

from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from core.config import Config, ConfigError
from core.exceptions import NotAuthorized
from schemas.core import ErrorSchema


def add_exception_handlers(app: FastAPI):
    """
    Добавляет обработчики для ошибок к сервису
    :param app: экземпляр сервиса
    :return:
    """
    logger = logging.getLogger("exception")

    @app.exception_handler(NotAuthorized)
    async def jwt_exception(request: Request, e: NotAuthorized):
        """
        Обработчик для ошибок авторизации
        """
        return JSONResponse(ErrorSchema(detail=str(e)).dict(), status_code=401)

    @app.exception_handler(IntegrityError)
    async def exists_exception(request: Request, e: IntegrityError):
        """
        Обработчик для ошибок отсутствия сущностей в базе
        """
        msg = str(e).split("DETAIL")[1].split("\n")[0]
        logger.error(f"db error {msg}", exc_info=True)
        return fastapi.Response("Internal Server Error", status_code=500)

    @app.exception_handler(ConfigError)
    async def config_error_exception(request: Request, e: ConfigError):
        """
        Попытка использования функционала, требующего отсутствующие переменные среды
        """
        logger.error("Enable it on service, please", exc_info=True)
        return JSONResponse(ErrorSchema(detail=str(e)).dict(), status_code=503)

    @app.exception_handler(Exception)
    async def internal_exception(request: Request, e: Exception):
        logger.error(f"Error occurred: {e}", exc_info=True)
        if Config.debug_mode:
            return JSONResponse({"detail": str(e), "traceback": traceback.format_exc()}, status_code=500)
        else:
            return fastapi.Response("Internal Server Error", status_code=500)
