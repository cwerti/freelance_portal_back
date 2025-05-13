import datetime

import pydantic
from pydantic import model_validator

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
