from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.base.auth.permissions import get_superuser, CurrentUser
from backend.app.base.utils.deps import SessionDep
from backend.app.models.auth import Msg
from backend.app.models.users import UserPublic, UserUpdate, UpdatePassword
from backend.app.repositories.user_repositories import user_repo

user_router = APIRouter()


@user_router.get('/me', response_model=UserPublic)
def user_me(current_user: CurrentUser):
    return current_user


@user_router.patch("/me", response_model=UserPublic)
async def update_user_me(*, db: SessionDep, schema: UserUpdate, user: CurrentUser) -> Any:
    return await user_repo.update_user(db=db, model=user, schema=schema)


@user_router.patch("/me/password", response_model=Msg)
async def update_password_me(*, db: SessionDep, schema: UpdatePassword, user: CurrentUser) -> Any:
    return await user_repo.update_password(db=db, schema=schema, model=user)


@user_router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(user_id: int, db: SessionDep, ) -> Any:
    return await user_repo.get_user_by_id(db, user_id=user_id)


@user_router.delete("/delete/{user_id}", response_model=Msg)
async def delete_user(user_id: int, db: SessionDep, user: CurrentUser) -> Msg:
    return await user_repo.delete_user(db=db, user=user, user_id=user_id)
