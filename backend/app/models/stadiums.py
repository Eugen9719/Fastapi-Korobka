from pydantic import ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum as PyEnum
from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field, Relationship


class ImageBase(SQLModel):
    images: str
    stadiums_id: int


class Image(ImageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    stadiums_id: int = Field(default=None, foreign_key="stadiums.id")
    stadium: Optional["Stadiums"] = Relationship(back_populates="images_all")


class StadiumStatus(str, PyEnum):
    ADDED = "added"
    REJECTED = "rejected"
    VERIFICATION = 'verification'
    NEEDS_REVISION = "needs_revision"


class StadiumsBase(SQLModel):
    name: str
    slug: str = Field(..., max_length=100, description="SLUG")
    address: str
    description: Optional[str] = Field(None, description="Описание")
    additional_info: Optional[str] = Field(None, description="Дополнительная информация")
    price: Decimal = Field(..., gt=0, description="Цена продукта",
                           sa_column=Column(Numeric(precision=10, scale=2)))
    country: str
    city: str


class Stadiums(StadiumsBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    updated_at: datetime = Field(default_factory=datetime.now, description="Дата последнего обновления")
    is_active: bool = Field(default=False, description="Флаг активности продукта")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: StadiumStatus = Field(default=StadiumStatus.VERIFICATION, nullable=True)
    reason: Optional[str] = Field(default=None, nullable=True)

    images_all: List[Image] = Relationship(back_populates="stadium")
    bookings: List["Booking"] = Relationship(back_populates="stadium", cascade_delete=True)
    owner: "User" = Relationship(back_populates="stadiums")
    stadium_reviews: List[Optional["StadiumReview"]] = Relationship(back_populates="stadium", sa_relationship_kwargs={
        "cascade": "all, delete-orphan"})

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = datetime.now()

    def __str__(self):
        return self.name


class StadiumReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", )
    stadium_id: int = Field(foreign_key="stadiums.id", description="ID связанного поля")
    review: str = Field(...)
    data: datetime = Field(default_factory=datetime.now, description="Дата создания  отзыва")

    stadium: Optional[Stadiums] = Relationship(back_populates="stadium_reviews")
    user_review: Optional["User"] = Relationship(back_populates="reviews")


# class AdditionalService(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(max_length=255)
#     description: Optional[str] = Field(default=None)
#     price: float  # Цена за услугу
#     stadium_id: int = Field(foreign_key="stadiums.id")
#     stadium: Optional["Stadiums"] = Relationship(back_populates="services")
#



class ImageCreate(ImageBase):
    pass


class ImageUpdate(ImageBase):
    pass


class StadiumsCreate(StadiumsBase):
    pass


class StadiumsUpdate(StadiumsBase):
    pass


class UserRead(SQLModel):
    first_name: str
    last_name: str


class StadiumVerificationUpdate(SQLModel):
    status: StadiumStatus
    reason: Optional[str] | None = None


class CreateReview(SQLModel):
    review: str


class UpdateReview(SQLModel):
    review: str


class ReviewRead(SQLModel):
    id: Optional[int]
    user_id: int
    stadium_id: int
    review: str
    data: datetime


class StadiumsRead(StadiumsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    user_id: int
    owner: Optional[UserRead]  # Включение данных о владельце
    images_all: List[Image]  # Включить список изображений
    stadium_reviews: List[StadiumReview] = []

    model_config = ConfigDict(from_attributes=True)
