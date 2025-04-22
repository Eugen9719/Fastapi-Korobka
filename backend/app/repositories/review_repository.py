from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.repositories.i_review_repo import IReviewRepository
from backend.app.models import StadiumReview
from backend.app.models.stadiums import CreateReview, UpdateReview
from backend.app.repositories.base_repositories import AsyncBaseRepository, QueryMixin


class ReviewRepository(IReviewRepository, AsyncBaseRepository[StadiumReview, CreateReview, UpdateReview], QueryMixin):
    def __init__(self):
        super().__init__(StadiumReview)


    async def check_duplicate_review(self, db: AsyncSession, user_id: int, stadium_id: int):
         return await self.exist(db=db, user_id=user_id, stadium_id=stadium_id)



