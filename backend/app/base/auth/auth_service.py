import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.core.security import get_password_hash
from .send_email import send_new_account_email, send_reset_password_email
from backend.core.config import settings
from ...models.auth import VerificationCreate, VerificationOut
from ...models.users import UserCreate, UserUpdateActive
from ...repositories.auth_repositories import auth_repo
from ...repositories.user_repositories import user_repo

password_reset_jwt_subject = 'present'


async def registration_user(new_user: UserCreate, db: AsyncSession):
    # Проверяем, существует ли пользователь с таким email
    existing_user = await user_repo.get_by_email(db, email=new_user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    user = await user_repo.create(db, schema=new_user)
    verify = await auth_repo.create(db, schema=VerificationCreate(user_id=user.id))
    send_new_account_email(new_user.email, new_user.full_name(), new_user.password, verify.link)
    return {"msg": "Письмо с подтверждением отправлено"}



async def verify_registration_user(uuid: VerificationOut, db: AsyncSession):
    verify = await auth_repo.get(db, link=uuid.link)
    if not verify:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification failed")
    user = await user_repo.get_or_404(db=db, id=verify.user_id)
    # Обновление данных пользователя (активация)
    update_data = {"is_active": True}
    user_update_schema = UserUpdateActive(**update_data)
    await user_repo.update(db, model=user, schema=user_update_schema)
    await auth_repo.remove(db, link=uuid.link)
    return {"msg": "Email successfully verified"}


async def password_recovery(db: AsyncSession, email, ):
    user = await user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='The user with this username does not exist in the system')
    password_reset_token = generate_password_reset_token(email)
    send_reset_password_email(email_to=user.email, email=email, token=password_reset_token)
    return {"msg": "Password recovery email sent"}


async def password_reset(db: AsyncSession, token: str, new_password: str):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = await user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="The user with this username does not exist in the system")

    if not user_repo.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    hashed_password = get_password_hash(new_password)
    await user_repo.update_password(db, user, hashed_password)
    return {"msg": "Password updated successfully"}


def generate_password_reset_token(email: str):
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {
            "exp": exp,
            "nbf": now.timestamp(),  # Убедитесь, что `now.timestamp()` используется
            "sub": password_reset_jwt_subject,
            "email": email
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("Decoded token:", decoded_token)  # Выводим содержимое токена
        assert decoded_token["sub"] == password_reset_jwt_subject, "Subject does not match"
        return decoded_token["email"]
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
    except AssertionError as e:
        print(f"Assertion error: {e}")
    return None
