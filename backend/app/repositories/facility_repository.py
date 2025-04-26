import logging
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.base.i_base_repo import CreateType, ModelType
from backend.app.interface.repositories.i_facility_repo import IFacilityRepository
from backend.app.models.additional_facility import AdditionalFacility, FacilityCreate, FacilityUpdate
from backend.app.repositories.base_repositories import AsyncBaseRepository, QueryMixin

logger = logging.getLogger(__name__)


class FacilityRepository(IFacilityRepository, AsyncBaseRepository[AdditionalFacility, FacilityCreate, FacilityUpdate],
                         QueryMixin):
    def __init__(self):
        super().__init__(AdditionalFacility)

    async def create_multiple(self, db: AsyncSession, schema: List[CreateType], **kwargs) -> List[ModelType]:
        """
        Создает несколько объектов в базе данных.
        """

        db_objs = [self.model(**s.model_dump(), **kwargs) for s in schema]  # Составляем список объектов
        db.add_all(db_objs)
        await db.commit()

            # Обновляем все объекты
        for obj in db_objs:
            await db.refresh(obj)

        return db_objs


    async def get_facility(self, db: AsyncSession, facility_id: int) -> Optional[AdditionalFacility]:
        result = await db.execute(
            select(AdditionalFacility).where(AdditionalFacility.id == facility_id)
        )
        return result.scalar_one_or_none()
