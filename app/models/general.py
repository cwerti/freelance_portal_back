from typing import Any
import os
import imghdr
from uuid import UUID

from sqlalchemy import (
    Column, DateTime, Integer, String, Boolean, Text, ForeignKey,
    Index, CheckConstraint, Numeric, text
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from models.core import Base, TimestampMixin, fresh_timestamp


def attachment_is_image_default(context: Any) -> bool:
    return is_image(context.get_current_parameters()["path"])


def is_image(path: os.PathLike) -> bool:
    return imghdr.what(path) is not None


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("users_email_key", "email", unique=True),
        CheckConstraint("email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'",
                        name="valid_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(128), nullable=False, unique=True)
    email = Column(String(256), nullable=False)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    password = Column(String(256))
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    role = relationship("Roles", back_populates="users")


class Roles(TimestampMixin, Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(String(300), nullable=True)

    users = relationship("User", back_populates="role")


class Files(TimestampMixin, Base):
    """Модель файлов системы."""

    __repr_name__ = "Файл"
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    name = Column(String(512))
    path = Column(String)
    is_image = Column(
        Boolean,
        nullable=False,
        server_default="false",
        default=attachment_is_image_default,
        comment="является ли данный файл изображением",
    )
