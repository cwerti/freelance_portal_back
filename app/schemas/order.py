from schemas.core import Model
from typing import Optional
from datetime import datetime
from pydantic import Field


class OrderModel(Model):
    author_id: int
    name: str
    description: str
    start_price: int
    deadline: datetime
    category_id: int
    status_id: int = Field(default=1)

class OrderStatusModel(Model):
    name: str
    description: str

class OrderUpdate(Model):
    name: Optional[str] = None
    description: Optional[str] = None
    start_price: Optional[float] = None
    category_id: Optional[int] = None
    status_id: Optional[int] = None

class CategoryOut(Model):
    id: int
    name: str
    description: str | None

class OrderOut(Model):
    id: int
    name: str
    description: Optional[str]