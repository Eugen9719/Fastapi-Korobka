from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.interface.base.i_base_repo import IReadRepository, ICrudRepository, CreateType, ModelType
from backend.app.models import AdditionalFacility
from backend.app.models.additional_facility import FacilityCreate, FacilityUpdate


class IFacilityRepository(IReadRepository[AdditionalFacility],
                          ICrudRepository[AdditionalFacility, FacilityCreate, FacilityUpdate], ABC):

    @abstractmethod
    async def create_multiple(self, db: AsyncSession, schema: List[CreateType], **kwargs) -> List[ModelType]:
        pass

    @abstractmethod
    async def get_facility(self, db: AsyncSession, facility_id: int) -> Optional[AdditionalFacility]:
        pass
