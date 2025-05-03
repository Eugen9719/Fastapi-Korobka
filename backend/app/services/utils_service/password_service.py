from datetime import timedelta, datetime
from typing import Optional
import jwt

from backend.app.interface.utils.i_password_service import IPasswordService
from backend.core.config import settings


# Реализация сервиса паролей
class PasswordService(IPasswordService):
    def hash_password(self, password: str) -> str:
        from backend.core.security import get_password_hash
        return get_password_hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        from backend.core.security import verify_password
        return verify_password(plain, hashed)

    def generate_password_reset_token(self, email: str):

        delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
        now = datetime.now()
        expires = now + delta
        exp = expires.timestamp()
        encoded_jwt = jwt.encode(
            {
                "exp": exp,
                "nbf": now.timestamp(),
                "sub": settings.password_reset_jwt_subject,
                "email": email
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt


    def verify_password_reset_token(self, token: str) -> Optional[str]:
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            print("Decoded token:", decoded_token)  # Выводим содержимое токена
            assert decoded_token["sub"] == settings.password_reset_jwt_subject, "Subject does not match"
            return decoded_token["email"]
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
        except AssertionError as e:
            print(f"Assertion error: {e}")
        return None
