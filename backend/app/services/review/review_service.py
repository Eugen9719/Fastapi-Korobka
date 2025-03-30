import logging

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models import User
from backend.app.models.auth import Msg
from backend.app.models.stadiums import  CreateReview, UpdateReview
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.repositories.stadiums_repositories import StadiumRepository
from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper

from backend.app.services.redis import RedisClient


logger = logging.getLogger(__name__)

class ReviewService:
    def __init__(self,stadium_repository: StadiumRepository, review_repository: ReviewRepository, permission: PermissionService, redis: RedisClient):
        self.stadium_repository = stadium_repository
        self.review_repository = review_repository
        self.permission = permission
        self.redis = redis

    @HttpExceptionWrapper
    async def create_review(self, db: AsyncSession, schema: CreateReview, stadium_id: int, user: User):
        stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
        if await self.review_repository.check_duplicate_review(db=db, user_id=user.id, stadium_id=stadium_id):
            raise HTTPException(status_code=400, detail="Вы уже оставили отзыв для этого стадиона")
        review = await self.review_repository.create_review(db=db, schema=schema, stadium_id=stadium.id, user_id=user.id)
        logger.info(f"отзыв {review.id} успешно создан пользователем {user.id}")
        return review

    @HttpExceptionWrapper
    async def update_review(self, db: AsyncSession, schema: UpdateReview, review_id: int, user: User):
        review = await self.review_repository.get_or_404(db=db, id=review_id)
        self.permission.check_current_user_or_admin(current_user=user, model=review)
        review = self.review_repository.update_review(db=db, model=review, schema=schema)
        logger.info(f"отзыв {review_id} успешно обновлен пользователем {user.id}")
        return review

    @HttpExceptionWrapper
    async def delete_review(self, db: AsyncSession, user: User, review_id: int):
        review = await self.review_repository.get_or_404(db=db, id=review_id)
        self.permission.check_current_user_or_admin(current_user=user, model=review)
        await self.review_repository.delete_review(db=db, review_id=review.id)
        logger.info(f"отзыв {review_id} успешно удален пользователем {user.id}")
        return Msg(msg="отзыв успешно удален")
