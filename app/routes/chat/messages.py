import fastapi
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.chats import get_chat, create_message, get_message

from schemas.chats import MessageCreate

from utils.auth.passwwords import get_token
from utils.database_connection import db_async_session

message = fastapi.APIRouter()


@message.post(
    "/message/create",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def message_create_route(
        message_info: MessageCreate,
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    res = await create_message(session, message_info)
    return res


@message.get(
    "/message/{message_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_chat_route(
        message_id: int = fastapi.Path(..., ge=1),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    chat = await get_message(session, message_id)
    return chat
