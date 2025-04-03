from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.dependencies.services import user_auth, permission_service, registration_service, user_service
from backend.app.models.auth import Token, Msg, VerificationOut
from backend.app.models.users import UserCreate
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core import security
from backend.core.config import settings
from backend.core.db import SessionDep, TransactionSessionDep

auth_router = APIRouter()


@auth_router.post("/login/access-token", response_model=Token)
@sentry_capture_exceptions
async def login_access_token(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Аутентификация пользователя и получение JWT токена.

    :param db: Сессия базы данных
    :param form_data: Данные формы авторизации (username=email, password)
    :return: Объект Token с access_token и типом bearer
    :raises HTTPException: 400 если email или пароль неверные
    """
    user = await user_auth.authenticate(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    permission_service.verify_active(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ), token_type="bearer"
    )


@auth_router.post("/registration", response_model=Msg)
@sentry_capture_exceptions
async def user_registration(new_user: UserCreate, db: TransactionSessionDep):
    """
    Регистрация нового пользователя.

    :param db: Сессия базы данных
    :param new_user: Данные для регистрации нового пользователя
    :return: Сообщение об успешной регистрации
    """
    return await registration_service.register_user(db=db, new_user=new_user)


@auth_router.post("/confirm_email", response_model=Msg)
@sentry_capture_exceptions
async def confirm_email(uuid: VerificationOut, db: TransactionSessionDep):
    """
    Подтверждение email пользователя по verification token.

    :param db: Сессия базы данных
    :param uuid: Объект с verification token
    :return: Сообщение об успешном подтверждении email
    """
    return await registration_service.verify_user(db=db, uuid=uuid)


@auth_router.post("/password-recovery/{email}", response_model=Msg)
@sentry_capture_exceptions
async def recover_password(email: str, db: SessionDep):
    """
    Запрос на восстановление пароля.

    :param db: Сессия базы данных
    :param email: Email для восстановления пароля
    :return: Сообщение о результате операции
    """
    return await user_service.password_recovery(db, email)


@auth_router.post("/reset_password", response_model=Msg)
@sentry_capture_exceptions
async def reset_password(db: TransactionSessionDep, token: str = Body(...), new_password: str = Body(...)):
    """
    Сброс пароля пользователя по токену из email.

    :param db: Сессия базы данных
    :param token: Токен для сброса пароля
    :param new_password: Новый пароль пользователя
    :return: Сообщение об успешном изменении пароля
    """
    return await user_service.password_reset(db, token, new_password)