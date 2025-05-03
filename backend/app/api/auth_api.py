from typing import Annotated

from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm


from backend.app.dependencies.service_factory import service_factory
from backend.app.models.auth import Token, Msg, VerificationOut
from backend.app.models.users import UserCreate
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core import security

from backend.core.db import SessionDep, TransactionSessionDep
from backend.core.oauth_config import oauth
from backend.core.security import verify_refresh_token


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
    user = await service_factory.user_auth.authenticate(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    service_factory.permission_service.verify_active(user)

    return Token(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
        token_type="bearer"
    )


from fastapi import Request, HTTPException
import logging

# Настройка логгера
logger = logging.getLogger(__name__)


@auth_router.get("/login/google")
async def login_google(request: Request):
    try:
        redirect_uri = request.url_for('auth_google')
        return await oauth.google.authorize_redirect(request, redirect_uri=redirect_uri)
    except Exception as e:
        logger.error(f"Error in Google login redirect: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initiate Google login")


@auth_router.get("/google", name='auth_google')
async def auth_google(request: Request, db: TransactionSessionDep):
   return await service_factory.user_auth.google_authenticate(request=request, db=db)

@auth_router.post("/refresh-token", response_model=Token)
@sentry_capture_exceptions
async def refresh_token(db: SessionDep, refresh_token: str = Body(..., embed=True)):
    """
    Обновление access токена с помощью refresh токена

    :param db: Сессия базы данных
    :param refresh_token: Refresh токен
    :return: Новая пара токенов
    :raises HTTPException: 401 если токен невалиден
    """
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
        user = await service_factory.user_service.get_or_404(db, object_id=user_id)
        service_factory.permission_service.verify_active(user)
        return Token(
                access_token=security.create_access_token(user.id),
                refresh_token=security.create_refresh_token(user.id),
                token_type="bearer"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
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
    return await service_factory.registration_service.register_user(db=db, schema=new_user)


@auth_router.post("/confirm_email", response_model=Msg)
@sentry_capture_exceptions
async def confirm_email(uuid: VerificationOut, db: TransactionSessionDep):
    """
    Подтверждение email пользователя по verification token.

    :param db: Сессия базы данных
    :param uuid: Объект с verification token
    :return: Сообщение об успешном подтверждении email
    """
    return await service_factory.registration_service.verify_user(db=db, uuid=uuid)


@auth_router.post("/password-recovery/{email}", response_model=Msg)
@sentry_capture_exceptions
async def recover_password(email: str, db: SessionDep):
    """
    Запрос на восстановление пароля.

    :param db: Сессия базы данных
    :param email: Email для восстановления пароля
    :return: Сообщение о результате операции
    """
    return await service_factory.user_service.password_recovery(db, email)


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
    return await service_factory.user_service.password_reset(db, token, new_password)