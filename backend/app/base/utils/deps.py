from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from sqlmodel import Session

from backend.core.config import settings
from backend.core.db import engine
from sqlalchemy.ext.asyncio import AsyncSession

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token", auto_error=False
)


# def get_db() -> Generator[Session, None, None]:
#     with Session(engine) as db:
#         yield db

async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as db:
        yield db



SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
