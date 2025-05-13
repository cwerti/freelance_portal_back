from uuid import uuid4

import fastapi
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotAuthorized
from internal.files import save_upload_file, save_file_db, get_file
from internal.users.users import user_exists, user_create, get_user
from models.general import User
from schemas.users import RegisterUserIn
from utils.auth.passwwords import verify_password, create_access_token, get_token
from utils.database_connection import db_async_session

files = fastapi.APIRouter()


@files.post(
    "/create",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def file_create(
        token: str = Depends(get_token),
        path: str = fastapi.Query('/src', ),
        is_image: bool = fastapi.Query(True, ),
        file: fastapi.UploadFile = fastapi.File(..., title="multipart файл"),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    """
    Загружает файл на сервер.

    После загрузки файла его можно получить по id файла
    """

    if path is None:
        path = "/src"
    path = "/" + path
    file.filename = uuid4().hex
    path = await save_upload_file(file, path)
    file = await save_file_db(session, path, file, is_image)
    return file


@files.get(
    "/{file_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_file_all(
        file_id: int = fastapi.Path(..., ge=1),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    """
    Получить все файлы.
    """
    file = await get_file(session, file_id)
    return file
