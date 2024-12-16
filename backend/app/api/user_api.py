from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.base.auth.permissions import get_superuser, CurrentUser
from backend.app.base.utils.deps import SessionDep
from backend.app.models.auth import Msg
from backend.app.models.users import UserPublic, UserUpdate, UpdatePassword
from backend.app.repositories.user_repositories import user_repository

from backend.core.security import verify_password, get_password_hash

user_router = APIRouter()


@user_router.get('/me', response_model=UserPublic)
def user_me(current_user: CurrentUser):
    """ Get user"""
    return current_user


@user_router.patch("/me", response_model=UserPublic)
def update_user_me(*, db: SessionDep, schema: UserUpdate, current_user: CurrentUser) -> Any:
    """Обновления текущего пользователя"""
    existing_user = user_repository.get_by_email(db=db, email=schema.email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Email is already in use by another user.")
    updated_user = user_repository.update(db=db, model=current_user, schema=schema)
    return updated_user


@user_router.patch("/me/password", response_model=Msg)
def update_password_me(*, db: SessionDep, schema: UpdatePassword, current_user: CurrentUser) -> Any:
    """
    Обновления пароля текущего пользователя
    """
    if not verify_password(schema.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if schema.current_password == schema.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(schema.new_password)
    user_repository.update_password(db=db, obj=current_user, hashed_password=hashed_password)
    return Msg(msg="Password updated successfully")


@user_router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(user_id: int, db: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get a specific user by id.
    """
    user = user_repository.get_or_404(db, id=user_id)
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


# @user_router.get("/", dependencies=[Depends(get_superuser)], response_model=List[UserPublicAdmin])
# def read_users(db: SessionDep, skip: int = 0, limit: int = 100):
#     """
#     Получить пользователей для супер юзера.
#     """
#
#     return user_crud.admin_user.all(db=db, skip=skip, limit=limit)


# @user_router.patch("/update/{user_id}", dependencies=[Depends(get_superuser)], response_model=UserPublicAdmin)
# def update_user(*, db: SessionDep, user_id: int, schema: UserUpdateAdmin) -> Any:
#     """
#     Обновления юзера в админке
#     """
#     db_user = user_crud.admin_user.get(db, id=user_id)
#     if not db_user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this id does not exist in the system",
#         )
#
#     existing_user = user_crud.user.get_by_email(db=db, email=schema.email)
#     if existing_user and existing_user.id != user_id:
#         raise HTTPException(
#             status_code=409, detail="User with this email already exists"
#         )
#     db_user = user_crud.user.update(db=db, model=db_user, schema=schema)
#     return db_user


""" Нужно решить удаления самого себя суперпользователем"""


@user_router.delete("/delete/{user_id}", response_model=Msg, dependencies=[Depends(get_superuser)])
def delete_user(user_id: int, db: SessionDep, current_user: CurrentUser) -> Msg:
    """
    Удаление пользователя.
    """
    user = user_repository.get_or_404(db, id=user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )

    # Удаление пользователя
    user_repository.remove(db, id=user.id)

    return Msg(msg="User deleted successfully")
