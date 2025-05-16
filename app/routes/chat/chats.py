import fastapi
import jwt
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core import Config
from internal.chats import create_chat, get_chat, get_my_chats

from schemas.chats import ChatCreate

from utils.auth.passwwords import get_token
from utils.database_connection import db_async_session

chats = fastapi.APIRouter()


@chats.post(
    "/create",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def chat_create(
        chat_info: ChatCreate,
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    res = await create_chat(chat_info, session)
    return res


@chats.get(
    "/{chat_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_chat_route(
        chat_id: int = fastapi.Path(..., ge=1),
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    chat = await get_chat(session, chat_id)
    return chat


@chats.get(
    "/{chat_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_chat_route(
        chat_id: int = fastapi.Path(..., ge=1),
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    chat = await get_chat(session, chat_id)
    return chat


@chats.post(
    "/get_my_chats",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_chat_route(
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    print("\n\n\n\n\n\n")
    print(token)
    qwe = jwt.decode(token, Config.SECRET_KEY, Config.ALGORITHM)
    res = await get_my_chats(session, qwe["id"])
    return res
