from schemas.core import Model
from datetime import datetime
from typing import Optional

class Order(Model):
    id: int
    author_id: int
    name: str
    description: str
    start_price: int
    deadline: datetime
    category_id: int