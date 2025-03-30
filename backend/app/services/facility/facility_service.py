import logging
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models import User
from backend.app.models.additional_facility import FacilityCreate
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper

logger = logging.getLogger(__name__)


class FacilityService:

    def __init__(self, facility_repository: FacilityRepository, permission: PermissionService):
        self.facility_repository = facility_repository
        self.permission = permission

    @HttpExceptionWrapper
    async def create_facility(self, db: AsyncSession, schema: List[FacilityCreate], user: User):
        # добавить проверку на владельца или админа
        facility = await self.facility_repository.create_multiple(db=db, schema=schema)
        logger.info(f"Услуги {facility} успешно создан пользователем {user.id}")
        return facility
