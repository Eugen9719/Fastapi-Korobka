from datetime import timedelta

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.repositories.user_repositories import user_repo
from backend.core import security
from backend.core.config import settings


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str, db: Session) -> None:
        super().__init__(secret_key)
        self.db = db

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form["username"], form["password"]

        # Логика аутентификации
        user = user_repo.authenticate(db=self.db, email=email, password=password)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
        elif not user_repo.is_active(user):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        # Создание токена доступа
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(user.id, expires_delta=access_token_expires)

        # Сохранение токена в сессии
        request.session.update({"token": token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        return True

# Передача экземпляра `db` при создании экземпляра `AdminAuth`
# db_instance = next(get_db())
# authentication_backend = AdminAuth(secret_key="your-secret-key", db=db_instance)