
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.models.users import User, UserCreate, UserUpdate
from backend.app.repositories.base_repositories import AsyncBaseRepository, QueryMixin




class UserRepository(IUserRepository, AsyncBaseRepository[User, UserCreate, UserUpdate], QueryMixin):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Получение пользователя по email."""
        return await self.get(db, email=email)




