
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum as PyEnum
from sqlalchemy import Column, Numeric
from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.base_model_public import ReviewReadBase, StadiumsReadBase, AdditionalFacilityReadBase


class ImageBase(SQLModel):
    url: str

class Image(ImageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    stadium_id: int = Field(default=None, foreign_key="stadium.id")
    stadium: Optional["Stadium"] = Relationship(back_populates="images_all")

class ImageCreate(ImageBase):
    pass
class ImageUpdate(ImageBase):
    pass



class StadiumReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", )
    stadium_id: int = Field(foreign_key="stadium.id", description="ID связанного поля")
    review: str = Field(...)
    data: datetime = Field(default_factory=datetime.now, description="Дата создания  отзыва")

    stadium: Optional["Stadium"] = Relationship(back_populates="stadium_reviews")
    user_review: Optional["User"] = Relationship(back_populates="reviews")

class ReviewRead(ReviewReadBase):
    pass


class CreateReview(SQLModel):
    review: str
class UpdateReview(SQLModel):
    review: str


class StadiumStatus(str, PyEnum):
    ADDED = "Added"
    REJECTED = "Rejected"
    VERIFICATION = 'Verification'
    NEEDS_REVISION = "Needs_revision"
    DRAFT = "Draft"


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


class Stadium(StadiumsBase, table=True):
    __tablename__ = 'stadium'
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    image_url: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    updated_at: datetime = Field(default_factory=datetime.now, description="Дата последнего обновления")
    is_active: bool = Field(default=False, description="Флаг активности продукта")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    status: StadiumStatus = Field(default=StadiumStatus.DRAFT, nullable=True)
    reason: Optional[str] = Field(default=None, nullable=True)

    # Связи с другими моделями
    images_all: List[Image] = Relationship(back_populates="stadium")
    bookings: List["Booking"] = Relationship(back_populates="stadium", cascade_delete=True)
    owner: "User" = Relationship(back_populates="stadiums")
    stadium_reviews: List["StadiumReview"] = Relationship(back_populates="stadium", cascade_delete=True)
    stadium_facility: List["StadiumFacility"] = Relationship(back_populates="stadium")




    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = datetime.now()

    def __str__(self):
        return self.name


class StadiumFacility(SQLModel, table=True):
    __tablename__ = 'stadium_facility'
    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadium.id")
    facility_id: int = Field(foreign_key="additional_facility.id")
    stadium: Optional["Stadium"] = Relationship(back_populates="stadium_facility")
    facility: Optional["AdditionalFacility"] = Relationship(back_populates="stadium")



class StadiumFacilityCreate(SQLModel):
    facility_id: int

class StadiumsCreate(StadiumsBase):
    pass

class StadiumsUpdate(StadiumsBase):
    is_active: bool = False

class StadiumVerificationUpdate(SQLModel):
    is_active: bool | None = None
    status: StadiumStatus
    reason: Optional[str] | None = None




class StadiumsRead(StadiumsReadBase):
    pass


class StadiumsReadWithFacility(StadiumsReadBase):
    stadium_reviews: List[ReviewReadBase]
    stadium_facility: Optional[List[AdditionalFacilityReadBase]] = None


class PaginatedStadiumsResponse(SQLModel):
    items: List[StadiumsRead]
    page: int
    pages: int