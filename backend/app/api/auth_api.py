from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from backend.app.base.auth.auth_service import registration_user, verify_registration_user, \
    generate_password_reset_token, verify_password_reset_token, password_recovery, password_reset
from backend.app.base.auth.send_email import send_reset_password_email
from backend.app.base.utils.deps import SessionDep

from backend.app.models.auth import Token, Msg, VerificationOut
from backend.app.models.users import UserCreate
from backend.app.repositories.user_repositories import user_repository
from backend.core import security
from backend.core.config import settings
from backend.core.security import get_password_hash

auth_router = APIRouter()


@auth_router.post("/login/access-token", response_model=Token)
def login_access_token(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = user_repository.authenticate(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    elif not user_repository.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user')

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ), token_type="bearer"
    )


@auth_router.post("/registration", response_model=Msg)
def user_registration(new_user: UserCreate, db: SessionDep):
    user = registration_user(new_user, db)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"msg": "Send email"}


@auth_router.post("/confirm_email", response_model=Msg)
def confirm_email(uuid: VerificationOut, db: SessionDep):
    if verify_registration_user(uuid, db):
        return {"msg": "Success verify email"}
        # return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    else:
        # Если подтверждение не удалось, возвращаем ошибку 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification failed")


@auth_router.post("/password-recovery/{email}", response_model=Msg)
def recover_password(email: str, db: SessionDep):
    password_recovery(db, email)
    return {"msg": "Password recovery email sent"}


@auth_router.post("/reset_password", response_model=Msg)
def reset_password(db: SessionDep, token: str = Body(...), new_password: str = Body(...), ):
    password_reset(db, token, new_password)
    return {"msg": "Password updated successfully"}
