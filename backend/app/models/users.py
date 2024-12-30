from datetime import datetime
from enum import Enum as PyEnum

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import ConfigDict

from backend.app.models import Order
from backend.app.models.base_model_public import UserReadBase
from backend.app.models.bookings import Booking

from backend.app.models.stadiums import Stadiums, StadiumReview


class StatusEnum(str, PyEnum):
    OWNER = "OWNER"
    PLAYER = "PLAYER"


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = Field(default=None, max_length=500)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    is_active: bool = Field(default=False)
    is_superuser: bool = Field(default=False)
    hashed_password: str
    last_login: Optional[datetime] = None
    status: StatusEnum = Field(default=StatusEnum.PLAYER)
    reviews: List["StadiumReview"] = Relationship(back_populates="user_review")

    bookings: List["Booking"] = Relationship(back_populates="user")
    stadiums: List["Stadiums"] = Relationship(back_populates="owner")
    orders: List["Order"] = Relationship(back_populates="user")

    def __str__(self):
        return f"{self.full_name()} ({self.email})"


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)
    status: StatusEnum = Field(default=StatusEnum.PLAYER)


class UserCreateAdmin(UserBase):
    password: str = Field(min_length=8, max_length=40)
    is_active: bool
    is_superuser: bool


class UserUpdateActive(SQLModel):
    is_active: Optional[bool]


class UserUpdate(UserBase):
    pass


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UserUpdateAdmin(UserBase):
    is_active: bool
    is_superuser: bool
    status: StatusEnum = Field(default=StatusEnum.PLAYER)


class UserPublic(UserReadBase):
    status: StatusEnum

    model_config = ConfigDict(from_attributes=True)
