"""
Стартовая настройка для sqlalchemy
"""
import datetime
import enum
from collections.abc import Callable

from sqlalchemy import MetaData, func, Column, DateTime
from sqlalchemy.orm import DeclarativeMeta, declarative_base

Base: DeclarativeMeta = declarative_base()
metadata: MetaData = Base.metadata
metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def fresh_timestamp() -> Callable[[], datetime.datetime]:
    """Небольшой хелпер для работы с timestamp на уровне ОРМа."""
    return func.timezone("UTC", func.now())


class TimestampMixin:
    created_at = Column(DateTime, default=fresh_timestamp())
    updated_at = Column(DateTime, default=fresh_timestamp(), onupdate=fresh_timestamp())
    deleted_at = Column(DateTime)


class Source(str, enum.Enum):
    """
    Источник, из которого был получен пользователь
    """

    system = "system"
    esia = "esia"
