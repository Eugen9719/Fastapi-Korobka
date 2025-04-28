from typing import Annotated
import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from fastapi import Depends, HTTPException, status

from backend.app.dependencies.service_factory import service_factory
from backend.app.models.auth import TokenPayload
from backend.app.models.users import User
from backend.app.services.auth.permission import PermissionService

from backend.core.config import settings


from backend.core.db import SessionDep




reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token", auto_error=False
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]




async def get_current_user(db: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
    user = await service_factory.user_repo.get_or_404(db=db, object_id=token_data.sub)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def active_user_required(user: CurrentUser) -> User:
    """Проверяет, что пользователь активен"""
    PermissionService.verify_active(user)
    return user

async def owner_required(user: CurrentUser) -> User:
    """Проверяет права владельца"""
    PermissionService.verify_owner(user)
    return user

async def superuser_required(user: CurrentUser) -> User:
    """Проверяет права суперпользователя"""
    PermissionService.verify_superuser(user)
    return user



OwnerUser = Annotated[User, Depends(owner_required)]
SuperUser = Annotated[User, Depends(superuser_required)]
