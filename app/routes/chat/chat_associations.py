import fastapi
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.chats import create_associations, get_associations
from internal.files import get_file
from schemas.chats import AssociationsCreate

from utils.auth.passwwords import get_token
from utils.database_connection import db_async_session

associations = fastapi.APIRouter()


@associations.post(
    "/associations/create",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def associations_create(
        associations_info: AssociationsCreate,
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    res = await create_associations(session, associations_info)
    return res


@associations.get(
    "/associations/{chat_id}",
    status_code=201,
    responses={409: {"description": "User with specified login or email already exists"}}
)
async def get_associations_route(
        chat_id: int = fastapi.Path(..., ge=1),
        token: str = Depends(get_token),
        session: AsyncSession = fastapi.Depends(db_async_session),
):
    associations = await get_associations(session, chat_id)
    return associations
