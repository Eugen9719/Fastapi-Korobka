import logging
from typing import List
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User
from backend.app.models.stadiums import StadiumFacilityCreate, StadiumFacility
from backend.app.services.utils_service.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.redis import RedisClient

logger = logging.getLogger(__name__)


class StadiumFacilityService:
    """Сервис управления стадионом"""

    def __init__(self, stadium_repository: IStadiumRepository, permission: PermissionService, redis: RedisClient):
        self.stadium_repository = stadium_repository
        self.permission = permission
        self.redis = redis

    @HttpExceptionWrapper
    async def add_facility_stadium(self, db: AsyncSession, stadium_id: int,
                                   facility_schema: List[StadiumFacilityCreate], user: User):

        stadium = await self.stadium_repository.get_or_404(db, object_id=stadium_id)
        self.permission.check_owner_or_admin(user, stadium)

        added = 0
        for facility in facility_schema:
            if not await self.stadium_repository.service_exists(db, facility.facility_id):
                raise HTTPException(404, f"Сервис с ID {facility.facility_id} не найден")

                # 2.2. Проверяем, что сервис еще не добавлен
            if await self.stadium_repository.is_service_linked(db, stadium_id, facility.facility_id):
                continue

            await self.stadium_repository.link_service_to_stadium(
                db, stadium_id, facility.facility_id
            )
            added += 1

        if added == 0:
            raise HTTPException(400, "Нет новых сервисов для добавления")
        await self.redis.delete_cache_by_prefix("stadiums:")
        return {f"message": f"Добавлено {added} сервисов"}

    @HttpExceptionWrapper
    async def delete_facility_from_stadium(self, db: AsyncSession, user: User, stadium_id: int,
                                           facility_id: int) -> dict:
        """
        Удаляет связь сервиса со стадионом.
        """

        # 1. Проверка прав доступа
        stadium = await self.stadium_repository.get_or_404(db, object_id=stadium_id)
        self.permission.check_owner_or_admin(user, stadium)

        deleted_facility_id = await self.stadium_repository.delete_relation(db=db, model=StadiumFacility,
                                                                            stadium_id=stadium_id,
                                                                            relation_id=facility_id)
        if deleted_facility_id is None:
            raise HTTPException(status_code=404, detail="Связь сервиса со стадионом не найдена")

        # 3. Инвалидация кеша (перед коммитом для атомарности)
        await self.redis.delete_cache_by_prefix(f"stadium:{stadium_id}:")

        logger.info(
            f"Удален сервис {facility_id} со стадиона {stadium_id} "
            f"пользователем {user.id}"
        )

        return {
            "status": "success",
            "message": "Связь сервиса со стадионом успешно удалена"
        }
