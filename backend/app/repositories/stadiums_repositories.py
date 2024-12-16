from datetime import datetime
from typing import Any, Sequence

from fastapi import HTTPException
from sqlalchemy import Row
from sqlmodel import Session, select

from .base_repositories import BaseRepository
from ..models import Booking
from ..models.stadiums import StadiumsCreate, Stadiums, StadiumsUpdate, StadiumReview, CreateReview, UpdateReview, \
    StadiumVerificationUpdate


class StadiumRepository(BaseRepository[Stadiums, StadiumsCreate, StadiumsUpdate]):

    def slug_unique(self, db: Session, slug: str) -> bool:
        return self.get_by_filter(db, self.model.slug == slug) is None

    def verification(self, db: Session, model: Stadiums, schema: StadiumVerificationUpdate):
        return super().update(db=db, model=model, schema=schema)

    def get_available_stadiums(self, db: Session, city: str, start_time: datetime, end_time: datetime) -> Sequence[
        Row[tuple[Any, ...] | Any]]:
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

        return db.exec(available_stadiums).all()


stadium_repo = StadiumRepository(Stadiums)


class ReviewRepository(BaseRepository[StadiumReview, CreateReview, UpdateReview]):

    def check_duplicate_review(self, db: Session, user_id:int, stadium_id:int):
        exists = self.exist(db=db,user_id=user_id, stadium_id=stadium_id)
        if exists:
            raise HTTPException(status_code=400, detail="Вы уже оставили отзыв для этого стадиона")




review_repo = ReviewRepository(StadiumReview)
