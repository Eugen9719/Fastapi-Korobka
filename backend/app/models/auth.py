from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import uuid4


class Verification(SQLModel, table=True):
    """ Модель для подтверждения регистрации пользователя"""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    link: str = Field(default_factory=lambda: str(uuid4()), index=True)
    user_id: int = Field(foreign_key="services.id")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"



class Msg(BaseModel):
    msg: str


class VerificationOut(BaseModel):
    link: str


class VerificationCreate(BaseModel):
    """"""
    user_id: int


class TokenPayload(BaseModel):
    sub: int | None = None



