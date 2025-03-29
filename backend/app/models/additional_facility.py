from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class AdditionalFacility(SQLModel, table=True):
    __tablename__ = 'additional_facility'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    svg_image: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=0.0, nullable=True)

    stadium: Optional[List["StadiumFacility"]] = Relationship(back_populates="facility")
    booking: List["BookingFacility"] = Relationship(back_populates="facility")


class FacilityCreate(SQLModel):
    name: str = Field(max_length=255)
    svg_image: str
    description: Optional[str] = Field(default=None)
    price: float

class FacilityUpdate(SQLModel):
    name: str = Field(max_length=255)
    svg_image: str
    description: Optional[str] = Field(default=None)
    price: float

class StadiumFacilityDelete(SQLModel):
    stadium_id: int
    facility_id: int

class FacilityRead(SQLModel):
    id:int
    name: str
    svg_image: str
    description: Optional[str]
    price: float