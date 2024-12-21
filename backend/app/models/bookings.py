from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class BookingBase(SQLModel):

    start_time: Optional[datetime]
    end_time: Optional[datetime]


    @property
    def formatted_start_time(self):
        return self.start_time.strftime("%d/%m/%Y %H:%M:%S")

    @property
    def formatted_end_time(self):
        return self.end_time.strftime("%d/%m/%Y %H:%M:%S")




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



class BookingCreate(BookingBase):
    stadium_id: Optional[int]



class BookingUpdate(BookingBase):
    stadium_id: Optional[int]


class BookingRead(BookingBase):
    id: Optional[int]
    price: int
    stadium_id: Optional[int]
    user_id: Optional[int]


class BookingServiceCreate(SQLModel):
    service_id: int
    quantity:int = Field(default=1)


class BookingServiceAdd(SQLModel):
    service_ids: List[BookingServiceCreate] = []

    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [
                    {
                        "service_id": 1,
                        "quantity": 2

                    },
                    {
                         "service_id": 2,
                        "quantity": 1
                    }
                ]
            }
        }