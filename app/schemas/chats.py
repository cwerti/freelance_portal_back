import datetime
from typing import Optional

import pydantic
from pydantic import model_validator, Field

from models import Message, ChatUserAssociation
from schemas.core import Model


class ChatCreate(Model):
    name: str
    client_id: int = pydantic.Field(default=1)
    order_id: int = pydantic.Field(default=1)


class AssociationsCreate(Model):
    client_id: int = pydantic.Field(default=1)
    executor_id: int = pydantic.Field(default=2)
    chat_id: int = pydantic.Field(default=1)

    @model_validator(mode='after')
    def check_ids_not_equal(self) -> 'AssociationsCreate':
        if self.client_id == self.executor_id:
            raise ValueError("client_id and executor_id cannot be equal")
        return self


class MessageCreate(Model):
    author_id: int = pydantic.Field(default=1)
    chat_id: int = pydantic.Field(default=1)
    text: Optional[str] = Field(None)
    file_id: Optional[int] = Field(None, alias="fileId")

    @model_validator(mode='after')
    def validate_content(self) -> 'MessageCreate':
        if self.text is None and self.file_id is None:
            raise ValueError("Either text or file_id must be provided")
        return self


class GetAllChats(Model):
    last_message: dict
    chat_association: dict
