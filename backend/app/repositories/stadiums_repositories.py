import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from .base_repositories import AsyncBaseRepository, QueryMixin
from ..models import AdditionalFacility, Booking
from ..models.stadiums import StadiumsCreate, Stadium, StadiumsUpdate, StadiumFacility
logger = logging.getLogger(__name__)





class StadiumRepository(AsyncBaseRepository[Stadium, StadiumsCreate, StadiumsUpdate], QueryMixin):
    def __init__(self):
        super().__init__(Stadium)

    async def create_stadium(self, db: AsyncSession, schema: StadiumsCreate, user_id: int):
        """
        Создает новый стадион в базе данных.
        """
        return await super().create(db=db, schema=schema, user_id=user_id)

    async def update_stadium(self, db: AsyncSession, model: Stadium, schema: StadiumsUpdate):
        """
        Обновляет данные стадиона.
        """
        return await super().update(db=db, model=model, schema=schema)

    async def delete_stadium(self, db: AsyncSession, stadium_id: int):
        """
        Удаляет стадион.
        """
        return await super().remove(db=db, id=stadium_id)

    async def is_slug_unique(self, db: AsyncSession, slug: str) -> bool:
        """Проверка уникальности slug"""
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none() is None

    @staticmethod
    async def service_exists(db: AsyncSession, facility_id: int) -> bool:
        """Проверяет существование сервиса"""
        return await db.scalar(
            select(1).where(AdditionalFacility.id == facility_id)
        ) is not None

    @staticmethod
    async def is_service_linked(db: AsyncSession, stadium_id: int, facility_id: int) -> bool:
        """Проверяет, связан ли сервис со стадионом"""
        return await db.scalar(
            select(1).where(
                StadiumFacility.stadium_id == stadium_id,
                StadiumFacility.facility_id == facility_id
            )
        ) is not None

    @staticmethod
    async def link_service_to_stadium(db: AsyncSession,stadium_id: int,facility_id: int,   ) -> None:
        """Создает связь между стадионом и сервисом"""
        db.add(StadiumFacility(
            stadium_id=stadium_id,
            facility_id=facility_id,
        ))


    @staticmethod
    async def search_available_stadiums( db: AsyncSession, city: str, start_time: datetime, end_time: datetime):
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