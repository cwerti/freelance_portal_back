from typing import Any
import os
import imghdr

from sqlalchemy import (
    Column, DateTime, Integer, String, Boolean, Text, ForeignKey,
    Index, CheckConstraint, Numeric
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
        Index("users_email_key", "email",  unique=True),
        CheckConstraint("email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'",
                        name="valid_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    login = Column(String(128), nullable=True, unique=True)
    email = Column(String(256), nullable=False)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)

    # Связи
    role = relationship("Role", back_populates="users", uselist=False)
    orders = relationship("Order", back_populates="author")
    chats_as_executor = relationship(
        "Chat",
        foreign_keys="Chat.executor_id",
        back_populates="executor"
    )
    chats_as_client = relationship(
        "Chat",
        foreign_keys="Chat.client_id",
        back_populates="client"
    )
    files = relationship("File", back_populates="author")
    messages = relationship("Message", back_populates="author")
    reviews_as_executor = relationship(
        "Review",
        foreign_keys="Review.executor",
        back_populates="executor_user"
    )
    reviews_as_author = relationship(
        "Review",
        foreign_keys="Review.author",
        back_populates="author_user"
    )

    @validates('email')
    def validate_email(self, key, email):
        assert '@' in email, "Invalid email address"
        return email


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("name ~ '^[a-zA-Z0-9_ ]+$'", name="valid_role_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    is_core = Column(Boolean, server_default="false", nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship(
        "RolePermission",
        uselist=True,
        cascade="all, delete-orphan",
        back_populates="role"
    )


class RolePermission(TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("idx_role_permission", "role_id", "permission", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission = Column(Text, nullable=False)
    created_at = Column(DateTime, default=fresh_timestamp())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = relationship("Role", back_populates="permissions")


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("start_price >= 0", name="positive_price"),
        CheckConstraint("name <> ''", name="non_empty_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    preview = Column(Integer, ForeignKey("files.id"), nullable=False)
    author = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_price = Column(Numeric(10, 2), nullable=True)
    image_list = Column(Text)
    delta_time = Column(DateTime, nullable=True)

    # Связи
    author_user = relationship("User", back_populates="orders")
    preview_file = relationship("File", foreign_keys=[preview])
    chat = relationship("Chat", back_populates="order", uselist=False)


class Chat(TimestampMixin, Base):
    __repr_name__ = "Чаты"
    __tablename__ = "chats"
    __table_args__ = (
        CheckConstraint("executor_id <> client_id", name="different_users"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    # Связи
    executor = relationship(
        "User",
        foreign_keys=[executor_id],
        back_populates="chats_as_executor"
    )
    client = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="chats_as_client"
    )
    order = relationship("Order", back_populates="chat")
    messages = relationship("Message", back_populates="chat")


class Message(TimestampMixin, Base):
    __repr_name__ = "Сообщения"
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("text <> '' OR file_id IS NOT NULL", name="message_content"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    text = Column(Text, nullable=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)

    # Связи
    author = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")
    file = relationship("File")


class File(TimestampMixin, Base):
    __repr_name__ = "Файлы"
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("name <> ''", name="non_empty_filename"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(Text, nullable=False)
    is_image = Column(
        Boolean,
        nullable=False,
        server_default="false",
        default=attachment_is_image_default,
        comment="является ли данный файл изображением",
    )

    # Связи
    author = relationship("User", back_populates="files")
    messages = relationship("Message", back_populates="file")
    reviews = relationship("Review", back_populates="file")
    order_previews = relationship("Order", back_populates="preview_file")


class Review(TimestampMixin, Base):
    __repr_name__ = "Отзывы"
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("grade BETWEEN 1 AND 5", name="valid_grade"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    grade = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    executor = Column(Integer, ForeignKey("users.id"), nullable=False)
    author = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Связи
    file = relationship("File", back_populates="reviews")
    executor_user = relationship(
        "User",
        foreign_keys=[executor],
        back_populates="reviews_as_executor"
    )
    author_user = relationship(
        "User",
        foreign_keys=[author],
        back_populates="reviews_as_author"
    )
