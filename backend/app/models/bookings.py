from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic.v1 import validator
from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.base_model_public import BookingReadBase, UserReadBase, StadiumsReadBase


class BookingBase(SQLModel):
    start_time: datetime = Field(nullable=False)
    end_time: datetime = Field(nullable=False)




class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    stadium_id: int = Field(foreign_key="stadiums.id")
    price: float
    user: Optional["User"] = Relationship(back_populates="bookings")
    stadium: Optional["Stadiums"] = Relationship(back_populates="bookings")
    booking_services: List["BookingService"] = Relationship(back_populates="booking")

    def __str__(self):
        return f"Бронь № {self.id}"


class BookingService(SQLModel, table=True):
    __tablename__ = 'booking_service'
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    service_id: int = Field(foreign_key="additional_service.id")
    quantity: int = Field(default=1)
    total_price: float

    booking: Optional["Booking"] = Relationship(back_populates="booking_services")
    service: Optional["AdditionalService"] = Relationship(back_populates="booking")





class BookingCreate(SQLModel):
    start_time: datetime
    end_time: datetime
    stadium_id: int

    @validator('start_time', 'end_time', pre=True)
    def parse_datetime(self, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Некорректный формат даты и времени: {value}")
        return value


class BookingUpdate(BookingBase):
    stadium_id: Optional[int]


class BookingServiceCreate(SQLModel):
    service_id: int
    quantity: int = Field(default=1)

class StadiumRead(SQLModel):
    id: int
    name: str
    address: str
    description: Optional[str]
    additional_info: Optional[str]
    price: Decimal
    country: str
    city: str

class BookingRead(BookingReadBase):
    start_time: datetime
    end_time: datetime

class BookingReadGet(BookingReadBase):
    stadium: StadiumRead
    start_time: datetime
    end_time: datetime