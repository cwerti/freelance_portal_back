from schemas.core import Model
from models.general import BidStatus
from models.core import fresh_timestamp
from datetime import datetime
from pydantic import Field

class BidCreate(Model):
    user_id: int
    price: float
    comment: str

class BidResponse(Model):
    id: int
    price: float
    comment: str
    status: BidStatus
    created_at: datetime = Field(default=datetime.utcnow())

class NotificationResponse(Model):
    id: int
    message: str
    