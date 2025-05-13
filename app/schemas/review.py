from schemas.core import Model
from datetime import datetime
from typing import Optional

class ReviewBase(Model):
    comment: str
    rating: int

class ReviewUpdate(Model):
    comment: str = None
    rating: int = None

class Review(ReviewBase):
    id: int
    comment: str
    rating: int
    reviewer_id: int
    reviewed_id: int
    created_at: datetime