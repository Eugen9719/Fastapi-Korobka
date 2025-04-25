from datetime import datetime, time
from decimal import Decimal
from typing import Optional, List
from enum import Enum as PyEnum

from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Numeric, Time
from sqlmodel import SQLModel, Field, Relationship
from backend.app.models.base_model_public import ReviewReadBase, StadiumsReadBase, AdditionalFacilityReadBase


class PriceInterval(SQLModel, table=True):
    __tablename__ = 'price_interval'

    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadium.id")
    start_time: time = Field(sa_column=Column(Time), description="Начало интервала")
    end_time: time = Field(sa_column=Column(Time), description="Конец интервала")
    price: Decimal = Field(..., gt=0, description="Цена для интервала",
                           sa_column=Column(Numeric(precision=10, scale=2)))
    day_of_week: Optional[int] = Field(None, ge=0, le=6,
                                       description="День недели (0-6, где 0 - понедельник). None - ежедневно")

    stadium: "Stadium" = Relationship(back_populates="price_intervals")

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
    images_all: List["Image"] = Relationship(back_populates="stadium")
    bookings: List["Booking"] = Relationship(back_populates="stadium", cascade_delete=True)
    owner: "User" = Relationship(back_populates="stadiums")
    stadium_reviews: List["StadiumReview"] = Relationship(back_populates="stadium", cascade_delete=True)
    stadium_facility: List["StadiumFacility"] = Relationship(back_populates="stadium")

    price_intervals: List["PriceInterval"] = Relationship(back_populates="stadium", cascade_delete=True)
    default_price: Optional[Decimal] = Field(None, gt=0, description="Базовая цена (дефолтная)",
                                     sa_column=Column(Numeric(precision=10, scale=2)))




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


class PriceIntervalCreate(BaseModel):
    start_time: time
    end_time: time
    price: Decimal
    day_of_week: Optional[int] = None  # 0-6 (0=понедельник), None для ежедневно

    @classmethod
    @field_validator('end_time')
    def validate_time_range(cls, end_time: time, info):  # info вместо values в Pydantic v2
        if 'start_time' in info.data and end_time <= info.data['start_time']:
            raise ValueError("End time must be after start time")
        return end_time

    @classmethod
    @field_validator('day_of_week')
    def validate_day_of_week(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 6):
            raise ValueError("Day of week must be between 0 (Monday) and 6 (Sunday)")
        return v


class StadiumCreate(SQLModel):
    name: str
    slug: str
    address: str
    description: Optional[str] = None
    additional_info: Optional[str] = None
    country: str
    city: str
    image_url: Optional[str] = None
    is_active: bool = False
    default_price: int = None
    price_intervals: List[PriceIntervalCreate]

    @classmethod
    @field_validator('price_intervals')
    def validate_price_intervals(cls, v):
        if not v:
            raise ValueError("At least one price interval must be provided")
        return v




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