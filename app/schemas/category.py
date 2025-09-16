from pydantic import BaseModel, Field
from typing import Optional


class CreateCategory(BaseModel):
    name: str
    parent_id: Optional[int] = Field(default=None)

