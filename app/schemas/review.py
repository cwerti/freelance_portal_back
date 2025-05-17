from schemas.core import Model
from datetime import datetime
from typing import Optional

class ReviewBase(Model):
    comment: str
    rating: int

class ReviewModel(ReviewBase):
    comment: str
    rating: int
    reviewer_id: int
    reviewed_id: int
    created_at: datetime