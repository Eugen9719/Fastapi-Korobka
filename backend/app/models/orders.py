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

    created_at: datetime = Field(default_factory=datetime.utcnow)  # Время создания заказа

    @property
    def formatted_created_at(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M:%S")


class Order(OrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    total_price: int  # Общая стоимость заказа
    user_id: int = Field(foreign_key="user.id")
    booking_id: int = Field(foreign_key="booking.id")

    booking: "Booking" = Relationship()
    user: "User" = Relationship(back_populates="orders")
    # additional_services: List["OrderAdditionalService"] = Relationship(back_populates="order")

    def __str__(self):
        return f"Заказ №{self.id} для пользователя {self.user_id}, статус: {self.status}"


class OrderCreate(SQLModel):
    booking_id: int  # Идентификатор бронирования
    status: str = Field(default="pending")  # Статус заказа (по умолчанию "pending")

    # def __init__(self, booking_id: int, status: str = "pending"):
    #     self.booking_id = booking_id
    #     self.status = status
    #     # Вы можете рассчитать total_price, основываясь на информации из бронирования
    #     booking = booking_repo.get_or_404(id=booking_id)  # Получаем бронирование
    #     self.total_price = booking.price  # Пример, здесь цена будет из бронирования

# class OrderAdditionalService(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: int = Field(foreign_key="orders.id")
#     service_id: int = Field(foreign_key="additionalservice.id")
#     quantity: int = Field(default=1)  # Количество выбранной услуги
#     total_price: float = Field()  # Общая стоимость для этой услуги
#
#     order: Optional["Order"] = Relationship(back_populates="additional_services")
#     service: Optional["AdditionalService"] = Relationship()


