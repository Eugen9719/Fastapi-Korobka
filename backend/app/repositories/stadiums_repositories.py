import logging
from datetime import datetime, time
from typing import List, Type

from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_, SQLModel
from .base_repositories import AsyncBaseRepository, QueryMixin
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from ..models import AdditionalFacility, Booking
from ..models.stadiums import StadiumCreate, Stadium, StadiumsUpdate, StadiumFacility, PriceInterval, \
    PriceIntervalCreate

logger = logging.getLogger(__name__)


class StadiumRepository(IStadiumRepository, AsyncBaseRepository[Stadium, StadiumCreate, StadiumsUpdate], QueryMixin):
    def __init__(self):
        super().__init__(Stadium)

    async def is_slug_unique(self, db: AsyncSession, slug: str) -> bool:
        """Проверка уникальности slug"""
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none() is None

    async def service_exists(self, db: AsyncSession, facility_id: int) -> bool:
        """Проверяет существование сервиса"""
        return await db.scalar(
            select(1).where(AdditionalFacility.id == facility_id)
        ) is not None

    async def is_service_linked(self, db: AsyncSession, stadium_id: int, facility_id: int) -> bool:
        """Проверяет, связан ли сервис со стадионом"""
        return await db.scalar(
            select(1).where(
                StadiumFacility.stadium_id == stadium_id,
                StadiumFacility.facility_id == facility_id
            )
        ) is not None

    async def link_service_to_stadium(self, db: AsyncSession, stadium_id: int, facility_id: int, ) -> None:
        """Создает связь между стадионом и сервисом"""
        db.add(StadiumFacility(
            stadium_id=stadium_id,
            facility_id=facility_id,
        ))


    async def delete_relation(self, db: AsyncSession, model:Type[SQLModel],  stadium_id: int, relation_id: int):
        result = await db.execute(
            delete(model)
            .where(
                and_(
                    model.stadium_id == stadium_id,
                    model.id == relation_id
                )
            )
            .returning(model.id)
        )
        return result.scalar_one_or_none()



    async def search_available_stadiums(self, db: AsyncSession, city: str, start_time: datetime, end_time: datetime):
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
            select(Stadium)
            .where(Stadium.city == city)
            .where(Stadium.id.notin_(subquery))
        )

        # Выполняем запрос и возвращаем результат
        result = await db.execute(available_stadiums)
        return result.scalars().all()

    async def check_intersection(
            self,
            db: AsyncSession,
            stadium_id: int,
            start_time: time,
            end_time: time
    ) -> bool:
        result = await db.execute(
            select(PriceInterval)
            .where(
                PriceInterval.stadium_id == stadium_id,
                PriceInterval.start_time < end_time,
                PriceInterval.end_time > start_time
            )
        )
        return result.scalar_one_or_none() is not None

    async def check_time(self, start_time: time, end_time: time):
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="start_time должен быть меньше end_time")

    async def validate_price_interval(
            self,
            db: AsyncSession,
            stadium_id: int,
            start_time: time,
            end_time: time
    ):
        await self.check_time(start_time, end_time)

        # if await self.check_intersection(db, stadium_id, start_time, end_time):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Ценовой интервал пересекается с существующим."
        #     )

    async def add_price_intervals(
            self,
            db: AsyncSession,
            price_intervals: List[PriceIntervalCreate],  # <-- Явный тип
            stadium_id: int
    ):
        for interval in price_intervals:
            start_time = interval.start_time
            end_time = interval.end_time

            await self.validate_price_interval(db, stadium_id, start_time, end_time)

            db.add(PriceInterval(
                stadium_id=stadium_id,
                start_time=start_time,
                end_time=end_time,
                price=interval.price
            ))

        await db.flush()
