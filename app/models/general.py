from typing import Any
import os
import imghdr

from sqlalchemy import (
    Column, DateTime, Integer, String, Boolean, Text, ForeignKey,
    Index, CheckConstraint, Numeric, Table
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from pydantic import EmailStr

from models.core import Base, TimestampMixin, fresh_timestamp


def attachment_is_image_default(context: Any) -> bool:
    return is_image(context.get_current_parameters()["path"])


def is_image(path: os.PathLike) -> bool:
    return imghdr.what(path) is not None


# user_skill_association = Table(
#     'user_skills', Base.metadata,
#     Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
#     Column('skill_id', Integer, ForeignKey('skills.id'), primary_key=True)
# )


# class OrderStatus(Base):
#     __tablename__ = "order_statuses"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(20), nullable=False, unique=True)  # open, in_progress, completed, cancelled
#     description = Column(Text)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'",
                        name="valid_email"),
    )

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    login = Column(String(128), unique=True)
    email = Column(String(220), nullable=False)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    description = Column(Text)
    password = Column(String(256))

    role = relationship("Role", back_populates="users")
    # Связи для чатов где пользователь клиент
    client_chats = relationship(
        "Chat",
        foreign_keys="Chat.client_id",
        back_populates="client"
    )

    # Связи для ассоциаций где пользователь клиент
    client_associations = relationship(
        "ChatUserAssociation",
        foreign_keys="ChatUserAssociation.client_id",
        back_populates="client"
    )

    # Связи для ассоциаций где пользователь исполнитель
    executor_associations = relationship(
        "ChatUserAssociation",
        foreign_keys="ChatUserAssociation.executor_id",
        back_populates="executor"
    )
    reviews_as_reviewer = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    reviews_as_reviewed = relationship("Review", back_populates="reviewed", foreign_keys="Review.reviewed_id")
    # order_associations = relationship("OrderUserAssociation", back_populates="user")
    # messages = relationship("Message", back_populates="author")
    # client_chats = relationship("Chat", foreign_keys="Chat.client_id", back_populates="client")
    # skills = relationship("Skill", secondary=user_skill_association, back_populates="users")
    # bids = relationship("Bid", back_populates="freelancer")
    # executor_chats = relationship("Chat", foreign_keys="Chat.executor_id", back_populates="executor")


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    is_core = Column(Boolean, server_default="false")

    users = relationship("User", back_populates="role")

    # permissions = relationship("RolePermission", back_populates="role")


class Chat(TimestampMixin, Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, nullable=False)
    # order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    last_message_at = Column(DateTime)
    # order = relationship("Order")

    client = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="client_chats"
    )
    user_associations = relationship(
        "ChatUserAssociation",
        back_populates="chat"
    )


class ChatUserAssociation(TimestampMixin, Base):
    __tablename__ = "chat_user_associations"

    chat_id = Column(Integer, ForeignKey('chats.id'), primary_key=True)
    client_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    executor_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    client = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="client_associations"
    )

    executor = relationship(
        "User",
        foreign_keys=[executor_id],
        back_populates="executor_associations"
    )

    chat = relationship(
        "Chat",
        back_populates="user_associations"
    )


class File(TimestampMixin, Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    is_image = Column(
        Boolean,
        nullable=False,
        server_default="false",
        default=attachment_is_image_default,
    )

    # messages = relationship("Message", back_populates="file")
    reviews = relationship("Review", back_populates="file")
    # order_previews = relationship("Order", foreign_keys="Order.preview_id")

# class RolePermission(TimestampMixin, Base):
#     __tablename__ = "role_permissions"
#
#     role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
#     permission = Column(Text, primary_key=True)
#     created_at = Column(DateTime, default=fresh_timestamp())
#     created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
#
#     role = relationship("Role", back_populates="permissions")


# class Category(TimestampMixin, Base):
#     __tablename__ = "categories"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), nullable=False, unique=True)
#     description = Column(Text)
#     parent_id = Column(Integer, ForeignKey("categories.id"))
#
#     orders = relationship("Order", back_populates="category")


# class Order(TimestampMixin, Base):
#     __tablename__ = "orders"
#     __table_args__ = (
#         CheckConstraint("start_price >= 0", name="positive_price"),
#     )
#
#     id = Column(Integer, primary_key=True)
#     name = Column(Text, nullable=False)
#     description = Column(Text)
#     author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
#     start_price = Column(Numeric(10, 2))
#     expected_price = Column(Numeric(10, 2))
#     status_id = Column(Integer, ForeignKey("order_statuses.id"), nullable=False, server_default="1")  # default: open
#     deadline = Column(DateTime)
#
#     category = relationship("Category", back_populates="orders")
#     preview = relationship("File")
#     author = relationship("User", foreign_keys=[author_id])
#     status = relationship("OrderStatus")
#     chat = relationship("Chat", back_populates="order", uselist=False)
#     bids = relationship("Bid", back_populates="order")
#     user_associations = relationship("OrderUserAssociation", back_populates="order")
#
#
#
# class Message(TimestampMixin, Base):
#     __tablename__ = "messages"
#
#     id = Column(Integer, primary_key=True)
#     author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
#     text = Column(Text)
#     file_id = Column(Integer, ForeignKey("files.id"))
#     is_read = Column(Boolean, server_default="false")
#
#     author = relationship("User", back_populates="messages")
#     chat = relationship("Chat", back_populates="messages")
#     file = relationship("File")
#
#
class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="valid_rating"),
    )

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"))
    comment = Column(Text)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    file = relationship("File", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_as_reviewer")
    reviewed = relationship("User", foreign_keys=[reviewed_id], back_populates="reviews_as_reviewed")
#   order = relationship("Order", back_populates="reviews")
#
#
# class Skill(Base):
#     __tablename__ = "skills"
#     __table_args__ = (
#         Index("idx_skill_name", "name"),
#     )
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(50), unique=True, nullable=False)
#     description = Column(Text)
#
#     users = relationship("User", secondary=user_skill_association, back_populates="skills")
#
#
# class Bid(Base):
#     __tablename__ = "bids"
#     __table_args__ = (
#         Index("idx_bid_order_freelancer", "order_id", "freelancer_id"),
#         CheckConstraint("price > 0", name="positive_price"),
#     )
#
#     id = Column(Integer, primary_key=True)
#     order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
#     freelancer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     price = Column(Numeric(10, 2), nullable=False)
#     comment = Column(Text)
#     status = Column(String(20), default="pending")
#     created_at = Column(DateTime, server_default=func.now())
#     updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
#
#     # Отношения
#     order = relationship("Order", back_populates="bids")
#     freelancer = relationship("User", back_populates="bids")
