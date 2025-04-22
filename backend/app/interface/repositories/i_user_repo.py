from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.interface.base.i_base_repo import ICrudRepository, IReadRepository
from backend.app.models import User
from backend.app.models.users import UserCreate, UserUpdate


class IUserRepository(IReadRepository[User], ICrudRepository[User, UserCreate, UserUpdate], ABC):

    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        pass
