import fastapi
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Chat, ChatUserAssociation, User, File, Message
from schemas.chats import ChatCreate, AssociationsCreate, MessageCreate, GetAllChats


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
            status_code=401,
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


async def create_message(session: AsyncSession, message_info: MessageCreate) -> Message:
    client_exists = await session.get(User, message_info.author_id)
    chat_exists = await session.get(Chat, message_info.chat_id)

    if not all([client_exists, chat_exists]):
        raise fastapi.HTTPException(
            status_code=401,
            detail="User or chat not found"
        )

    if message_info.file_id is not None:
        file_exists = await session.get(File, message_info.chat_id)
        if file_exists is None:
            raise fastapi.HTTPException(
                status_code=400,
                detail="File not found"
            )

    new_message = (
        insert(Message)
        .values(
            author_id=message_info.author_id,
            chat_id=message_info.chat_id,
            text=message_info.text,
            file_id=message_info.file_id,
        )
        .returning(Message)
    )

    try:
        result = await session.execute(new_message)
        return result.scalar_one()
    except IntegrityError as e:
        await session.rollback()
        if "duplicate key" in str(e):
            raise fastapi.HTTPException(
                status_code=400,
                detail="Message already exists"
            )
        raise fastapi.HTTPException(
            status_code=500,
            detail="Database integrity error or File not found"
        )
    except Exception as e:
        await session.rollback()
        raise fastapi.HTTPException(
            status_code=500,
            detail=f"Failed to create message: {str(e)}"
        )


async def get_message(session: AsyncSession, message_id: int) -> Message:
    query = (
        select(Message)
        .where(Message.id == message_id)
        .order_by(Message.deleted_at.desc())
    )
    message = (await session.execute(query)).scalars().all()
    return message


async def all_message_chat(session: AsyncSession, associations_info: AssociationsCreate):
    client_exists = await session.get(User, associations_info.client_id)
    executor_exists = await session.get(User, associations_info.executor_id)
    chat_exists = await session.get(Chat, associations_info.chat_id)

    if not all([client_exists, chat_exists, client_exists, executor_exists]):
        raise fastapi.HTTPException(
            status_code=401,
            detail="Client or chat or executor not found"
        )

    try:
        association = await get_associations(session, associations_info.chat_id)
    except:
        association = await create_associations(session, associations_info)

    query = (
        select(Message)
        .where(Message.chat_id == associations_info.chat_id)
        .order_by(Message.deleted_at.desc())
    )

    messsages_list = (await session.execute(query)).scalars().all()
    return messsages_list


async def get_last_message(session: AsyncSession, chat_id) -> Message:
    chat_exists = await session.get(Chat, chat_id)

    if chat_exists is None:
        raise fastapi.HTTPException(
            status_code=401,
            detail="Chat not found"
        )

    query = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
    )
    message_last = (await session.execute(query)).scalars().first()
    return message_last


async def get_my_chats(session: AsyncSession, user_id) -> [GetAllChats, ...]:
    user_exists = await session.get(User, user_id)
    if user_exists is None:
        raise fastapi.HTTPException(
            status_code=401,
            detail="User not found"
        )
    query = (
        select(ChatUserAssociation)
        .where(ChatUserAssociation.client_id == user_id)
        .order_by(ChatUserAssociation.deleted_at.desc())
    )
    chat_association_list = (await session.execute(query)).scalars().all()
    result = []
    for chat_association in chat_association_list:
        last_message = await get_last_message(session, chat_association.chat_id)
        result.append({
            "last_message": last_message,
            "chat_association": chat_association
        })
    return result
