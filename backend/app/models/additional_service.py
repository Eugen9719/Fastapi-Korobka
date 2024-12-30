from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class AdditionalService(SQLModel, table=True):
    __tablename__ = 'additional_service'
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    price: float
    stadium_id: int = Field(foreign_key="stadiums.id")  # stadiums.id должно быть правильно указано в lower case

    stadium: Optional["Stadiums"] = Relationship(back_populates="services")
    booking: List["BookingService"] = Relationship(back_populates="service")


class AdditionalServiceCreate(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    price: float


class StadiumServiceAdd(SQLModel):
    service_ids: List[int] = []
    new_services: List["AdditionalServiceCreate"] = []

    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [1, 2, 3],
                "new_services": [
                    {
                        "name": "Premium Parking",
                        "description": "Close to the main entrance",
                        "price": 10.99
                    },
                    {
                        "name": "VIP Lounge",
                        "description": "Exclusive access to VIP facilities",
                        "price": 50.00
                    }
                ]
            }
        }
