from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import uuid4, UUID


class Verification(SQLModel, table=True):
    """ Модель для подтверждения регистрации пользователя"""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    link: UUID = Field(default_factory=uuid4, index=True)
    user_id: int = Field(foreign_key="user.id")


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"




class Msg(SQLModel):
    msg: str


class VerificationOut(SQLModel):
    link: UUID


class VerificationCreate(SQLModel):
    """"""
    user_id: int


class TokenPayload(SQLModel):
    sub: int | None = None



class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
