from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateReview(BaseModel):
    user_id: int
    product_id: int
    rating_id: Optional[int] = Field(default_factory=None)
    comment: str
    comment_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
