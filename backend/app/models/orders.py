from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship


class StatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED="canceled"

class OrderBase(SQLModel):
    # Заказ будет содержать информацию о статусе, общей цене и времени оформления
    status: str = Field(default=StatusEnum.PENDING, max_length=50)  # Статус заказа: pending, completed, canceled



    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M:%S")


class Order(OrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Время создания заказа
    total_price: int  # Общая стоимость заказа
    user_id: int = Field(foreign_key="user.id")
    booking_id: int = Field(foreign_key="booking.id")

    booking: "Booking" = Relationship()
    user: "User" = Relationship(back_populates="orders")
    # additional_services: List["OrderAdditionalService"] = Relationship(back_populates="order")

    def __str__(self):
        return f"Заказ №{self.id} для пользователя {self.user_id}, статус: {self.status}"


class OrderCreate(OrderBase):
    booking_id: int  # Идентификатор бронирования


class OrderUpdate(OrderBase):
    pass


class UserRead(SQLModel):
    id: int
    email:str
    first_name: str
    last_name: str

class BookingRead(SQLModel):
    id: int
    user: Optional[int]
    stadium_id: int
    price: int

class OrderRead(OrderBase):
    id: Optional[int]
    created_at: datetime
    total_price: int
    user: Optional[UserRead]
    user_id: int = Field(foreign_key="user.id")
    booking:Optional[BookingRead]


# class OrderAdditionalService(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: int = Field(foreign_key="orders.id")
#     service_id: int = Field(foreign_key="additionalservice.id")
#     quantity: int = Field(default=1)  # Количество выбранной услуги
#     total_price: float = Field()  # Общая стоимость для этой услуги
#
#     order: Optional["Order"] = Relationship(back_populates="additional_services")
#     service: Optional["AdditionalService"] = Relationship()


