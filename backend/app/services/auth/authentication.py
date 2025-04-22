from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.interface.utils.i_password_service import IPasswordService
from backend.app.models import User
from backend.app.services.decorators import HttpExceptionWrapper


class UserAuthentication:
    """Сервис аутентификации пользователей"""

    def __init__(self, pass_service: IPasswordService, user_repository: IUserRepository):
        self.pass_service = pass_service
        self.user_repository = user_repository

    @HttpExceptionWrapper
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.user_repository.get_by_email(db, email=email)
        if not user or not self.pass_service.verify_password(password, user.hashed_password):
            return None
        return user
