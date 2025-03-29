from datetime import datetime
from decimal import Decimal
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


class AdditionalFacilityReadBase(SQLModel):
    id: int
    name: str
    svg_image: str
    description: str
    price: float


class StadiumsReadBase(SQLModel):
    id: int
    created_at: datetime
    updated_at: datetime
    status: str
    is_active: bool
    user_id: int
    name: str
    slug: str
    address: str
    description: Optional[str]
    additional_info: Optional[str]
    price: Decimal
    country: str
    city: str
    image_url: Optional[str]


class BookingReadBase(SQLModel):
    id: int
    user_id: Optional[int]
    stadium_id: int
    price_booking: float
    total_price: float
    status: str
    stripe_payment_intent_id: Optional[str]
