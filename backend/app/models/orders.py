from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.bookings import BookingServiceCreate


class StatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED="canceled"









class OrderBase(SQLModel):
    status: str = Field(default=StatusEnum.PENDING, max_length=50)


class Order(OrderBase, table=True):
    __tablename__ = 'order'
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_price: float
    user_id: int = Field(foreign_key="user.id")
    booking_id: int = Field(foreign_key="booking.id")

    booking: "Booking" = Relationship()
    user: "User" = Relationship(back_populates="orders")


    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M:%S")

    def __str__(self):
        return f"Заказ №{self.id} для пользователя {self.user_id}, статус: {self.status}"







class OrderCreate(OrderBase):
    booking_id: int  # Идентификатор бронирования
    services: Optional[List[BookingServiceCreate]] = None




class OrderUpdate(OrderBase):
    pass


class UserRead(SQLModel):
    id: int
    email:str
    first_name: str
    last_name: str

class BookingRead(SQLModel):
    id: int
    user_id: Optional[int]
    stadium_id: int
    price: int

class OrderRead(OrderBase):
    id: Optional[int]
    created_at: datetime
    total_price: int
    user: Optional[UserRead]
    user_id: int = Field(foreign_key="user.id")
    booking:Optional[BookingRead]





