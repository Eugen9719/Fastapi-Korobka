from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.base.auth.auth_service import registration_user, verify_registration_user, password_recovery, \
    password_reset

from backend.app.base.utils.deps import SessionDep

from backend.app.models.auth import Token, Msg, VerificationOut
from backend.app.models.users import UserCreate
from backend.app.repositories.user_repositories import user_repo
from backend.core import security
from backend.core.config import settings

auth_router = APIRouter()


@auth_router.post("/login/access-token", response_model=Token)
async def login_access_token(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await user_repo.authenticate(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    elif not user_repo.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user')

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ), token_type="bearer"
    )


@auth_router.post("/registration", response_model=Msg)
async def user_registration(new_user: UserCreate, db: SessionDep):
    return await registration_user(db=db, new_user=new_user)


@auth_router.post("/confirm_email", response_model=Msg)
async def confirm_email(uuid: VerificationOut, db: SessionDep):
    return await verify_registration_user(db=db, uuid=uuid)


@auth_router.post("/password-recovery/{email}", response_model=Msg)
async def recover_password(email: str, db: SessionDep):
    return await password_recovery(db, email)


@auth_router.post("/reset_password", response_model=Msg)
async def reset_password(db: SessionDep, token: str = Body(...), new_password: str = Body(...), ):
    return password_reset(db, token, new_password)
