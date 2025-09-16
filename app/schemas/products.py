from pydantic import BaseModel, Field
from typing import Optional


class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category: Optional[int] = Field(default=None)
