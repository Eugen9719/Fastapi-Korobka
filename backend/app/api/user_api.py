from typing import Any, List
from fastapi import APIRouter, UploadFile, File

from backend.app.dependencies.auth_dep import CurrentUser, SuperUser
from backend.app.dependencies.repositories import user_repo

from backend.app.dependencies.services import user_service
from backend.app.models.auth import Msg
from backend.app.models.users import UserPublic, UserUpdate, UpdatePassword
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import SessionDep


user_router = APIRouter()


@user_router.get('/me', response_model=UserPublic)

def user_me(current_user: CurrentUser):
    return current_user


@user_router.patch("/me", response_model=UserPublic)
@sentry_capture_exceptions
async def update_user_me(*, db: SessionDep, schema: UserUpdate, user: CurrentUser) -> Any:
    return await user_service.update_user(db=db, model=user, schema=schema)


@user_router.patch("/me/password", response_model=Msg)
@sentry_capture_exceptions
async def update_password_me(*, db: SessionDep, schema: UpdatePassword, user: CurrentUser) -> Any:
    return await user_service.update_password(db=db, schema=schema, model=user)


@user_router.patch("/upload-avatar")
@sentry_capture_exceptions
async def upload_image(db: SessionDep, user: CurrentUser, file: UploadFile = File(...)):
    return await user_service.upload_image(db, file=file, model=user)



@user_router.get("/all_user", response_model=List[UserPublic])
@sentry_capture_exceptions
async def get_all_user(db: SessionDep, user:SuperUser):
    return await user_repo.get_many(db=db)


@user_router.delete("/delete/{user_id}", response_model=Msg)
@sentry_capture_exceptions
async def delete_user(user_id: int, db: SessionDep, user: CurrentUser) -> Msg:
    return await user_repo.delete_user(db=db, current_user=user, user_id=user_id)

@user_router.get("/{user_id}", response_model=UserPublic)
@sentry_capture_exceptions
async def read_user_by_id(user_id: int, db: SessionDep,user:SuperUser ) -> Any:
    return await user_repo.get_or_404(db, id=user_id)