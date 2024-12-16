import jwt
from fastapi import HTTPException

from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from starlette import status

from backend.core.security import get_password_hash
from .send_email import send_new_account_email, send_reset_password_email
from backend.core.config import settings
from ...models.auth import VerificationCreate, VerificationOut
from ...models.users import UserCreate, UserUpdateActive
from ...repositories.auth_repositories import auth_repository
from ...repositories.user_repositories import user_repository

password_reset_jwt_subject = 'present'


def registration_user(new_user: UserCreate, db: Session):
    """Подтверждаем email пользователя"""
    if user_repository.get_by_email(db, email=new_user.email):
        return True
    else:
        user = user_repository.create(db, schema=new_user)
        verify = auth_repository.create(db, schema=VerificationCreate(user_id=user.id))
        send_new_account_email(new_user.email, new_user.full_name(), new_user.password, verify.link)
        return False


def verify_registration_user(uuid: VerificationOut, db: Session) -> bool:
    verify = auth_repository.get(
        db, link=uuid.link)
    if not verify:
        print(f"Verification not found for link: {uuid.link}")
        return False

    user = user_repository.get(db, id=verify.user_id)
    if not user:
        return False
    update_data = {"is_active": True}
    user_repository.update(db, model=user, schema=UserUpdateActive(**update_data))
    auth_repository.remove(db, link=uuid.link)
    print(f"User {user.email} activated successfully")
    return True


def password_recovery(db: Session, email, ):
    user = user_repository.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='The user with this username does not exist in the system')
    password_reset_token = generate_password_reset_token(email)
    send_reset_password_email(email_to=user.email, email=email, token=password_reset_token)



def password_reset(db: Session, token: str, new_password: str):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = user_repository.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="The user with this username does not exist in the system")

    if not user_repository.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    hashed_password = get_password_hash(new_password)
    user_repository.update_password(db, user, hashed_password)


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
