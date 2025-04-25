from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.base_model_public import ReviewReadBase


class StadiumReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", )
    stadium_id: int = Field(foreign_key="stadium.id", description="ID связанного поля")
    review: str = Field(...)
    data: datetime = Field(default_factory=datetime.now, description="Дата создания  отзыва")

    stadium: Optional["Stadium"] = Relationship(back_populates="stadium_reviews")
    user_review: Optional["User"] = Relationship(back_populates="reviews")

class ReviewRead(ReviewReadBase):
    pass


class CreateReview(SQLModel):
    review: str
class UpdateReview(SQLModel):
    review: str
