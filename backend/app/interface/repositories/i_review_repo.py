from abc import abstractmethod, ABC
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.interface.base.i_base_repo import ICrudRepository, IReadRepository
from backend.app.models.stadium_reviews import StadiumReview, CreateReview, UpdateReview


class IReviewRepository(IReadRepository[StadiumReview],ICrudRepository[StadiumReview, CreateReview, UpdateReview], ABC):

    @abstractmethod
    async def check_duplicate_review(self, db: AsyncSession, user_id: int, stadium_id: int):
        pass
