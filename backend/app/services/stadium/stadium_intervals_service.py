import logging
from typing import List
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User
from backend.app.models.auth import Msg
from backend.app.models.stadiums import StadiumStatus, PriceIntervalCreate, PriceInterval
from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.redis import RedisClient

logger = logging.getLogger(__name__)


class StadiumIntervalsService:
    """Сервис управления стадионом"""

    def __init__(self, stadium_repository: IStadiumRepository, permission: PermissionService, redis: RedisClient):
        self.stadium_repository = stadium_repository
        self.permission = permission
        self.redis = redis

    @HttpExceptionWrapper
    async def create_price_intervals(self, db: AsyncSession, schema: List[PriceIntervalCreate], stadium_id: int,
                                     user: User):
        update_stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
        self.permission.check_owner_or_admin(current_user=user, model=update_stadium)
        if update_stadium.status == StadiumStatus.VERIFICATION:
            raise HTTPException(status_code=400,
                                detail="вы не можете изменить объект, пока у него статус 'На верификации'")
        await self.stadium_repository.add_price_intervals(db=db, price_intervals=schema, stadium_id=stadium_id)
        return update_stadium

    @HttpExceptionWrapper
    async def delete_price_interval(self, db: AsyncSession, user: User, interval_id: int, stadium_id: int):
        """
        Удаляет ценовой интервал стадиона.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
        self.permission.check_owner_or_admin(current_user=user, model=stadium)

        was_active = stadium.is_active

        deleted_interval_id = await self.stadium_repository.delete_relation(db=db, model=PriceInterval, stadium_id=stadium_id,
                                                                   relation_id=interval_id)

        if deleted_interval_id is None:
            raise HTTPException(status_code=404, detail="Ценовой интервал не найден")

        if was_active:
            await self.redis.invalidate_cache("stadiums:all_active",
                                              f"Удаление ценового интервала {deleted_interval_id} стадиона {stadium_id}")

        logger.info(f"Ценовой интервал {deleted_interval_id} стадиона {stadium_id} удален пользователем {user.id}")

        return Msg(msg="Ценовой интервал был удален успешно")
