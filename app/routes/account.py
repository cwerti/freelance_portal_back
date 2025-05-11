import fastapi
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotAuthorized
from internal.users.users import user_exists, user_create, get_user
from models.general import User
from schemas.users import RegisterUserIn
from utils.auth.passwwords import verify_password, create_access_token, get_token
from utils.database_connection import db_async_session

auth = fastapi.APIRouter()


@auth.post(
    "/login",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}},
)
async def login(response: fastapi.Response,
                login: str = fastapi.Body(..., title="Почта или логин"),
                password: str = fastapi.Body(...),
                session: AsyncSession = fastapi.Depends(db_async_session),
                ):
    """
    Регистрация в системе.
    """

    incorrect_data_exception = NotAuthorized("Неверный логин или пароль")

    user: User = await user_exists(session, login, login, include_deleted=True)

    if not user:
        raise incorrect_data_exception

    user = await user_exists(session, login, login)

    if (not user) or (not verify_password(password, user.password)):
        raise incorrect_data_exception
    else:
        access_token = create_access_token(data={"sub": user.login})
        response.set_cookie(key="access_token", value=access_token, httponly=True)

    return user


@auth.post(
    "/register",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}},
)
async def register(
        user_info: RegisterUserIn,
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    """
    Регистрация в системе.
    """

    user_from_db: User = await user_exists(session, user_info.login, user_info.email, include_deleted=False)
    if user_from_db is not None:
        raise fastapi.HTTPException(
            400,
            detail={"message": "Такой пользователь уже существует"},
        )
    new_user: User = await user_create(session, user_info)
    return new_user


@auth.get(
    "/user/{user_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def user_info(
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
        user_id: int = fastapi.Path(..., ge=1),
):
    """
    Регистрация в системе.
    """
    user = await get_user(session, user_id)

    if not user:
        raise fastapi.HTTPException(
            400,
            detail={
                "user_id": user_id,
                "message": "Такой пользователь не найден"},
        )
    return user


@auth.post("/logout/")
async def logout_user(response: fastapi.Response):
    response.delete_cookie(key="access_token")
    return {'message': 'Пользователь успешно вышел из системы'}
