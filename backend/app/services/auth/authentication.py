import logging
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.interface.utils.i_password_service import IPasswordService
from backend.app.models import User
from backend.app.models.auth import Token
from backend.app.services.auth.google_auth_service import GoogleAuthService

from backend.app.services.decorators import HttpExceptionWrapper


logger = logging.getLogger(__name__)


class UserAuthentication:
    """Сервис аутентификации пользователей"""

    def __init__(self, pass_service: IPasswordService, user_repository: IUserRepository, google_auth_service: GoogleAuthService):
        self.pass_service = pass_service
        self.user_repository = user_repository
        self.google_auth_service = google_auth_service

    @HttpExceptionWrapper
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.user_repository.get_by_email(db, email=email)
        if not user or not self.pass_service.verify_password(password, user.hashed_password):
            return None
        return user

    @HttpExceptionWrapper
    async def google_authenticate(self, request: dict, db: AsyncSession) -> Token:
       return await self.google_auth_service.authenticate(db=db, request=request)


