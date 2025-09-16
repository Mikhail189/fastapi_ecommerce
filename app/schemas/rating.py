from pydantic import BaseModel


class CreateRating(BaseModel):
    grade: int
    user_id: int
    product_id: int
