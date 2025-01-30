from datetime import datetime
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from sqlmodel import select

from .base_repositories import AsyncBaseRepository
from ..models import Booking, User
from ..models.additional_service import StadiumServiceAdd, AdditionalService
from ..models.auth import Msg
from ..models.stadiums import StadiumsCreate, Stadiums, StadiumsUpdate, StadiumReview, CreateReview, UpdateReview, \
    StadiumVerificationUpdate, StadiumStatus


class StadiumRepository(AsyncBaseRepository[Stadiums, StadiumsCreate, StadiumsUpdate]):

    async def create_stadium(self, db: AsyncSession, schema: StadiumsCreate, user_id: int):
        if not await self.slug_unique(db, schema.slug):
            raise HTTPException(status_code=400, detail="Slug already used")
        return await super().create(db=db, schema=schema, user_id=user_id)

    async def verification(self, db: AsyncSession, schema: StadiumVerificationUpdate, stadium_id: int):
        "Нужно добавить проверку на админа"
        stadium = await self.get_or_404(db=db, id=stadium_id)
        is_active = True if schema.status == StadiumStatus.ADDED else False
        schema.is_active = is_active
        return await super().update(db=db, model=stadium, schema=schema)

    async def update_stadium(self, db: AsyncSession, schema: StadiumsUpdate, stadium_id: int, user: User):
        stadium = await self.get_or_404(db=db, id=stadium_id)
        self.check_current_user_or_admin(current_user=user, model=stadium)
        if not user.is_superuser:
            stadium.status = StadiumStatus.VERIFICATION
            stadium.is_active = False
        return await super().update(db=db, model=stadium, schema=schema)

    async def delete_stadium(self, db: AsyncSession, user: User, stadium_id: int):
        stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)
        stadium_repo.check_current_user_or_admin(current_user=user, model=stadium)
        await super().remove(db=db, id=stadium.id)
        return Msg(msg="stadium deleted successfully")

    async def add_services_stadium(self, stadium_id: int, schema: StadiumServiceAdd, db: AsyncSession):
        # Получаем стадион по id
        stadium = await self.get_or_404(db, stadium_id)

        # Привязываем существующие сервисы
        if schema.service_ids:
            existing_services = await db.execute(
                select(AdditionalService).filter(AdditionalService.id.in_(schema.service_ids))
            )
            existing_services = existing_services.scalars().all()
            if not existing_services:
                raise HTTPException(status_code=404, detail="Services not found")

            for service in existing_services:
                service.stadium_id = stadium.id

        # Добавляем новые сервисы
        if schema.new_services:
            new_services = [
                AdditionalService(
                    name=new_service.name,
                    description=new_service.description,
                    price=new_service.price,
                    stadium_id=stadium.id
                )
                for new_service in schema.new_services
            ]
            db.add_all(new_services)

        # Выполняем один коммит после всех изменений
        await db.commit()
        return stadium

    async def get_available_stadiums(self, db: AsyncSession, city: str, start_time: datetime, end_time: datetime) -> \
            Sequence[Stadiums]:
        # Подзапрос для поиска стадионов, которые уже забронированы в заданном диапазоне времени.
        subquery = (
            select(Booking.stadium_id)
            .where(
                (Booking.start_time < end_time) &
                (Booking.end_time > start_time)
            )
        )

        # Основной запрос для поиска доступных стадионов
        available_stadiums = (
            select(Stadiums)
            .where(Stadiums.city == city)
            .where(Stadiums.id.notin_(subquery))
        )

        # Выполняем запрос и возвращаем результат
        result = await db.execute(available_stadiums)
        return result.scalars().all()

    async def slug_unique(self, db: AsyncSession, slug: str) -> bool:
        return await self.get_by_filter(db, self.model.slug == slug) is None


stadium_repo = StadiumRepository(Stadiums)


class ReviewRepository(AsyncBaseRepository[StadiumReview, CreateReview, UpdateReview]):

    async def create_review(self, db: AsyncSession, schema: StadiumsCreate, stadium_id: int, user: User):
        stadium = await stadium_repo.get_or_404(db=db, id=stadium_id)
        await review_repo.check_duplicate_review(db=db, user_id=user.id, stadium_id=stadium_id)
        return await super().create(db=db, schema=schema, stadium_id=stadium.id, user_id=user.id)

    async def update_review(self, db: AsyncSession, schema: StadiumsUpdate, review_id: int, user: User):
        review = await review_repo.get_or_404(db=db, id=review_id)
        review_repo.check_current_user_or_admin(current_user=user, model=review)
        return await super().update(db=db, model=review, schema=schema)

    async def delete_review(self, db: AsyncSession, user: User, review_id: int):
        review = await review_repo.get_or_404(db, id=review_id)
        review_repo.check_current_user_or_admin(current_user=user, model=review)
        await super().remove(db=db, id=review.id)
        return Msg(msg="Review deleted successfully")

    async def check_duplicate_review(self, db: AsyncSession, user_id: int, stadium_id: int):
        exists = await self.exist(db=db, user_id=user_id, stadium_id=stadium_id)
        if exists:
            raise HTTPException(status_code=400, detail="Вы уже оставили отзыв для этого стадиона")


review_repo = ReviewRepository(StadiumReview)
