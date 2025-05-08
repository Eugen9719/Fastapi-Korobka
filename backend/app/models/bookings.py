from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic.v1 import validator
from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.base_model_public import BookingReadBase, StadiumsReadBase, UserReadBase


class StatusBooking(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELED = "Canceled"
    MANUAL = "Manual"


class BookingBase(SQLModel):
    start_time: datetime = Field(nullable=False)
    end_time: datetime = Field(nullable=False)


class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: Optional[int] = Field(foreign_key="services.id")
    stadium_id: int = Field(foreign_key="services.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default=StatusBooking.PENDING, max_length=50)
    stripe_payment_intent_id: Optional[str]
    price_booking: float
    total_price: float = Field(nullable=True)
    owner_stadium:int
    user: Optional["User"] = Relationship(back_populates="bookings")
    stadium: Optional["Stadium"] = Relationship(back_populates="bookings")

    # Добавлено cascade="all, delete-orphan"
    booking_facility: List["BookingFacility"] = Relationship(
        back_populates="services",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    status_note: str = Field(default="", nullable=True)  # Поле для пометки

    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M:%S")

    def __str__(self):
        return f"Бронь № {self.id}"


class BookingFacility(SQLModel, table=True):
    __tablename__ = 'booking_facility'
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="services.id")
    facility_id: int = Field(foreign_key="additional_facility.id")
    quantity: int = Field(default=1)
    total_price: float

    booking: Optional["Booking"] = Relationship(back_populates="booking_facility")
    facility: Optional["AdditionalFacility"] = Relationship(back_populates="services")


class BookingFacilityCreate(SQLModel):
    facility_id: int
    quantity: int = Field(default=1)


class BookingCreate(SQLModel):
    start_time: datetime
    end_time: datetime
    stadium_id: int
    status_note: Optional[str]=None
    list_facility: Optional[List[BookingFacilityCreate]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "2025-03-26T11:41:01.167",
                "end_time": "2025-03-26T12:41:01.167",
                "stadium_id": 1,
                "status_note": "Бронирование для тренировки",
                "services": [
                    {
                        "facility_id": 1,
                        "quantity": 2
                    }
                ]
            }
        }

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

class BookingFacilityRead(SQLModel):
    facility_id: int
    name:str
    quantity: int
    total_price: float

class BookingRead(BookingReadBase):
    start_time: datetime
    end_time: datetime


class BookingReadGet(BookingReadBase):
    stadium: StadiumsReadBase
    user: UserReadBase
    start_time: datetime
    end_time: datetime

class PaginatedBookingsResponse(SQLModel):
    items: List[BookingReadGet]
    page: int
    pages: int