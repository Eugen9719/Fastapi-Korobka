from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class UserReadBase(SQLModel):
    id: int
    email: str
    first_name: str
    last_name: str


class ReviewReadBase(SQLModel):
    id: Optional[int]
    user_id: int
    stadium_id: int
    review: str
    data: datetime


class AdditionalServiceReadBase(SQLModel):
    name: str
    description: Optional[str]
    price: float


class StadiumsReadBase(SQLModel):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    user_id: int




class BookingReadBase(SQLModel):
    id: int
    user_id: Optional[int]
    stadium_id: int
    price: int


class OrderReadBase(SQLModel):
    id: Optional[int]
    created_at: datetime
    total_price: int
    user_id: int
    booking_id: int
