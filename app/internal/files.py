import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

import aiofiles
from fastapi import UploadFile
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Files


async def save_file(
        file_data: bytes,
        upload_dir: str,
        *,
        filename: Optional[str] = None,
        allowed_extensions: Optional[list[str]] = None,
        max_size: int = 10 * 1024 * 1024  # 10MB по умолчанию
) -> str:
    """
    Асинхронно сохраняет файл на диск с проверками.

    Args:
        file_data: Бинарные данные файла
        upload_dir: Директория для сохранения
        filename: Имя файла (если None - сгенерируется UUID)
        allowed_extensions: Разрешенные расширения (['.jpg', '.png'])
        max_size: Максимальный размер файла в байтах

    Returns:
        Полный путь к сохраненному файлу

    Raises:
        ValueError: При нарушении проверок
        IOError: При ошибках записи
    """
    # Проверка размера файла
    if len(file_data) > max_size:
        raise ValueError(f"Файл слишком большой. Максимальный размер: {max_size} байт")

    # Создаем директорию, если не существует
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    # Генерируем имя файла если не указано

    if allowed_extensions:
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"Недопустимое расширение файла. Разрешены: {', '.join(allowed_extensions)}")

    file_path = Path(upload_dir) / filename

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
    except Exception as e:
        raise IOError(f"Ошибка при сохранении файла: {str(e)}")

    return str(file_path)


async def save_upload_file(
        upload_file: UploadFile,
        upload_dir: str,
        **kwargs
) -> str:
    """
    Сохраняет файл из FastAPI UploadFile.

    Args:
        upload_file: Объект UploadFile из FastAPI
        upload_dir: Директория для сохранения
        **kwargs: Доп. параметры (см. save_file)

    Returns:
        Полный путь к сохраненному файлу
    """
    file_data = await upload_file.read()

    if 'filename' not in kwargs:
        kwargs['filename'] = upload_file.filename

    return await save_file(file_data, upload_dir, **kwargs)


async def save_file_db(
        session: AsyncSession,
        path: str,
        file: UploadFile,
        is_image: bool = True,
) -> Files:
    file_insert = (
        insert(Files)
        .values(
            name=file.filename,
            path=path,
            is_image=is_image,
        )
        .returning(Files)
    )

    try:
        result = await session.execute(file_insert)
        return result.scalar_one()
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("Database integrity error occurred") from e
    except Exception as e:
        await session.rollback()
        raise ValueError("Failed to create file") from e


async def get_file(session: AsyncSession, user_id: int) -> Files:
    query = (
        select(Files)
        .where(Files.id == user_id)
        .order_by(Files.deleted_at.desc())
    )
    file = (await session.execute(query)).scalars().all()
    return file
