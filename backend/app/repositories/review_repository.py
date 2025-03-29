from sqlmodel.ext.asyncio.session import AsyncSession


from backend.app.abstractions.repository import ModelType
from backend.app.models import StadiumReview
from backend.app.models.stadiums import CreateReview, UpdateReview
from backend.app.repositories.base_repositories import AsyncBaseRepository, QueryMixin


class ReviewRepository(AsyncBaseRepository[StadiumReview, CreateReview, UpdateReview], QueryMixin):
    def __init__(self):
        super().__init__(StadiumReview)

    async def create_review(self, db: AsyncSession, schema: CreateReview, stadium_id: int, user_id: int):
        return await super().create(db=db, schema=schema, stadium_id=stadium_id, user_id=user_id)


    async def update_review(self, db: AsyncSession,model:ModelType, schema: UpdateReview, ):
        return await super().update(db=db, model=model, schema=schema)


    async def delete_review(self, db: AsyncSession, review_id: int):
        return await super().remove(db=db, id=review_id)

    async def check_duplicate_review(self, db: AsyncSession, user_id: int, stadium_id: int):
         return await self.exist(db=db, user_id=user_id, stadium_id=stadium_id)



