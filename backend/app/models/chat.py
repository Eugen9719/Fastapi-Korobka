from typing import Optional
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    sender_id: int = Field(foreign_key="services.id")
    recipient_id: int = Field(foreign_key="services.id")
    content: Optional[str] = Field(default=None, nullable=True)


class MessageCreate(SQLModel):
    recipient_id: int = Field(..., description="ID получателя сообщения")
    content: str = Field(..., description="Содержимое сообщения")


class MessageUpdate(SQLModel):
    id: Optional[int]
    content: str = Field(..., description="Содержимое сообщения")

class MessageRead(SQLModel):
    id: int = Field(..., description="Уникальный идентификатор сообщения")
    sender_id: int = Field(..., description="ID отправителя сообщения")
    recipient_id: int = Field(..., description="ID получателя сообщения")
    content: str = Field(..., description="Содержимое сообщения")