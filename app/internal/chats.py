import fastapi
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Chat, ChatUserAssociation, User
from schemas.chats import ChatCreate, AssociationsCreate


async def create_chat(
        chat_info: ChatCreate,
        session: AsyncSession,
) -> Chat:
    chat_insert = (
        insert(Chat)
        .values(
            name=chat_info.name,
            client_id=chat_info.client_id,
            order_id=chat_info.order_id
        )
        .returning(Chat)
    )

    try:
        result = await session.execute(chat_insert)
        return result.scalar_one()
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("Database integrity error occurred") from e
    except Exception as e:
        await session.rollback()
        raise ValueError("Failed to create chat") from e


async def get_chat(session: AsyncSession, chat_id: int) -> Chat:
    query = (
        select(Chat)
        .where(Chat.id == chat_id)
        .order_by(Chat.deleted_at.desc())
    )
    chat = (await session.execute(query)).scalars().all()
    return chat


async def create_associations(
        session: AsyncSession,
        associations_info: AssociationsCreate
) -> ChatUserAssociation:
    # Проверка что client_id != executor_id
    if associations_info.client_id == associations_info.executor_id:
        raise fastapi.HTTPException(
            status_code=400,
            detail="Client and executor cannot be the same"
        )

    # Проверка существования пользователей и чата
    client_exists = await session.get(User, associations_info.client_id)
    executor_exists = await session.get(User, associations_info.executor_id)
    chat_exists = await session.get(Chat, associations_info.chat_id)

    if not all([client_exists, executor_exists, chat_exists]):
        raise fastapi.HTTPException(
            status_code=404,
            detail="User or chat not found"
        )

    # Проверка существования ассоциации для этого чата
    existing_association = await session.execute(
        select(ChatUserAssociation)
        .where(ChatUserAssociation.chat_id == associations_info.chat_id)
    )

    if existing_association.scalar_one_or_none() is not None:
        raise fastapi.HTTPException(
            status_code=400,
            detail="Association for this chat already exists"
        )

    # Создание новой ассоциации
    new_association = (
        insert(ChatUserAssociation)
        .values(
            client_id=associations_info.client_id,
            executor_id=associations_info.executor_id,
            chat_id=associations_info.chat_id
        )
        .returning(ChatUserAssociation)
    )
    try:
        result = await session.execute(new_association)
        return result.scalar_one()
    except IntegrityError as e:
        await session.rollback()
        if "duplicate key" in str(e):
            raise fastapi.HTTPException(
                status_code=400,
                detail="Association already exists"
            )
        raise fastapi.HTTPException(
            status_code=500,
            detail="Database integrity error"
        )
    except Exception as e:
        await session.rollback()
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to create association: {str(e)}"
        )


async def get_associations(session: AsyncSession, chat_id: int) -> ChatUserAssociation:
    query = (
        select(ChatUserAssociation)
        .where(ChatUserAssociation.chat_id == chat_id)
        .order_by(ChatUserAssociation.deleted_at.desc())
    )
    associations = (await session.execute(query)).scalars().all()
    return associations
