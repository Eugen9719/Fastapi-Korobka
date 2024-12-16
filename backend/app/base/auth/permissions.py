from typing import Annotated
import jwt
from jwt import PyJWTError
from fastapi import Depends, HTTPException, status
from sqlmodel import select

from backend.app.models.auth import TokenPayload
from backend.app.models.users import User
from backend.app.repositories.user_repositories import user_repository
from backend.core.config import settings


from backend.app.base.utils.deps import TokenDep, SessionDep

# def get_current_user(db: SessionDep, token: TokenDep) -> User:
#     try:
#         payload = jwt.decode(
#             token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": True}
#         )
#         token_data = TokenPayload(**payload)
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек")
#     except PyJWTError:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Не удалось проверить учетные данные")
#
#     user = db.exec(select(User).filter_by(id=token_data.sub)).first()
#
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
#     return user

def get_current_user(db: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    user = db.exec(select(User).filter_by(id=token_data.sub)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owner(current_user: CurrentUser) -> User:
    if not user_repository.is_owner(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user not owner")
    return current_user


OwnerUser = Annotated[User, Depends(get_owner)]


def get_superuser(current_user: CurrentUser) -> User:
    if not user_repository.is_superuser(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The user doesn't have enough privileges")
    return current_user

SuperUser = Annotated[User, Depends(get_superuser)]