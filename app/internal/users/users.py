from typing import Optional

import fastapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select, insert
from sqlalchemy.exc import IntegrityError
from models import User, Role
from schemas.users import RegisterUserIn
from utils.auth.passwwords import generate_password_hash


async def user_exists(
        session: AsyncSession,
        login: str,
        email: str,
        user_id: int = None,
        include_deleted: bool = False,
        options=None,  # noqa: ANN001
) -> Optional[User]:
    """
    Проверка на существование юзера по логину или почте.

    При наличии нескольких пользователей под 1 почтой (если пользователь удалён, то его почта не уникальна)
    будет выдан неудалённый пользователь (при наличии)
    """
    users = await users_exists(session, login, email, user_id, include_deleted=include_deleted, options=options)
    return users[0] if len(users) > 0 else None


async def users_exists(
        session: AsyncSession,
        login: str,
        email: str,
        user_id: int = None,
        include_deleted: bool = False,
        options=None,  # noqa: ANN001
) -> list[User]:
    """Извращённая проверка на существование нескольких пользователей с указанными данными."""

    query = (
        select(User)
        .where(or_(func.lower(User.login) == func.lower(login), func.lower(User.email) == func.lower(email)))
        .order_by(User.deleted_at.desc())
    )

    if user_id:
        query = query.where(User.id != user_id)

    if not include_deleted:
        query = query.where(User.deleted_at.is_(None))

    if options:
        query = query.options(*options)

    users = (await session.execute(query)).scalars().all()

    return users


async def check_credentials(session: AsyncSession, login: str, email: str, user_id: int = None) -> None:  # noqa: C901
    """
    Проверка данных для регистрации или создания нового пользователя.

    :param session: сессия бд
    :param login: логин пользователя
    :param email: почта для пользователя
    :raises fastapi.HTTPException: 409 ошибка, при конфликте пользователей
    """
    # т.к. почта не уникальна, то нам нужно проверить всех пользователей
    if users := (await users_exists(session, login, email, include_deleted=True, user_id=user_id)):
        exists_exception = fastapi.HTTPException(
            409, detail="Пользователь с указанным логином или почтой уже существует"
        )

        # логин уникален и создавать второго такого нельзя
        for existing_user in users:
            if existing_user.login == login:
                raise exists_exception

        for existing_user in users:
            if existing_user.deleted_at is None:
                raise exists_exception
    await session.flush()


async def user_create(
        session: AsyncSession,
        user_data: RegisterUserIn,
        options: list | None = None
) -> User:
    role_check_query = select(Role).where(Role.id == user_data.role_id)
    if not (await session.execute(role_check_query)).scalar_one_or_none():
        raise fastapi.HTTPException(
            400,
            detail={
                "role_id": user_data.role_id,
                "message": "Такой роли не существуе"},
        )

    user_insert = (
        insert(User)
        .values(
            login=user_data.login,
            password=generate_password_hash(user_data.password),
            email=user_data.email,
            last_name=user_data.last_name,
            first_name=user_data.first_name,
            role_id=user_data.role_id
        )
        .returning(User)
    )

    if options:
        user_insert = user_insert.options(*options)

    try:
        result = await session.execute(user_insert)
        return result.scalar_one()
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("Database integrity error occurred") from e
    except Exception as e:
        await session.rollback()
        raise ValueError("Failed to create user") from e


async def get_user(session: AsyncSession, user_id: int) -> User:
    query = (
        select(User)
        .where(User.id == user_id)
        .order_by(User.deleted_at.desc())
    )
    user = (await session.execute(query)).scalars().all()
    return user