from abc import ABC, abstractmethod
from datetime import datetime
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from backend.app.interface.base.i_base_repo import ICrudRepository, IReadRepository, IPaginateRepository

from backend.app.models.additional_facility import StadiumFacilityDelete
from backend.app.models.stadiums import StadiumCreate, Stadium, StadiumsUpdate


class IStadiumRepository(IReadRepository[Stadium], IPaginateRepository[Stadium],
                         ICrudRepository[Stadium, StadiumCreate, StadiumsUpdate], ABC):

    @abstractmethod
    async def is_slug_unique(self, db: AsyncSession, slug: str) -> bool:
        pass

    @abstractmethod
    async def service_exists(self, db: AsyncSession, facility_id: int) -> bool:
        pass

    @abstractmethod
    async def is_service_linked(self, db: AsyncSession, stadium_id: int, facility_id: int) -> bool:
        pass

    @abstractmethod
    async def link_service_to_stadium(self, db: AsyncSession, stadium_id: int, facility_id: int, ) -> None:
        pass

    @abstractmethod
    async def search_available_stadiums(self, db: AsyncSession, city: str, start_time: datetime, end_time: datetime):
        pass




    @abstractmethod
    async def add_price_intervals(self, db,  price_intervals, stadium_id):
        pass

    @abstractmethod
    async def delete_relation(self, db: AsyncSession, model:Type[SQLModel],  stadium_id: int, relation_id: int):
        pass
