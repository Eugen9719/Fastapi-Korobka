from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class ImageBase(SQLModel):
    url: str

class Image(ImageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    stadium_id: int = Field(default=None, foreign_key="services.id")
    stadium: Optional["Stadium"] = Relationship(back_populates="images_all")

class ImageCreate(ImageBase):
    pass
class ImageUpdate(ImageBase):
    pass