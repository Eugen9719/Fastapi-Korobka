from datetime import datetime
from typing import Optional
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
    price: int
    user: Optional["User"] = Relationship(back_populates="bookings")
    stadium: Optional["Stadiums"] = Relationship(back_populates="bookings")

    def __str__(self):
        return f"Бронь № {self.id}"


class BookingCreate(BookingBase):
    stadium_id: Optional[int]



class BookingUpdate(BookingBase):
    stadium_id: Optional[int]


class BookingRead(BookingBase):
    id: Optional[int]
    price: int
    stadium_id: Optional[int]
    user_id: Optional[int]