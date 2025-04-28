import logging
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User
from backend.app.models.auth import Msg
from backend.app.models.stadiums import StadiumVerificationUpdate, StadiumStatus
from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.redis import RedisClient

logger = logging.getLogger(__name__)


class StadiumVerifService:
    """Сервис управления стадионом"""

    def __init__(self, stadium_repository: IStadiumRepository, permission: PermissionService, redis: RedisClient):
        self.stadium_repository = stadium_repository
        self.permission = permission
        self.redis = redis

    @HttpExceptionWrapper
    async def verify_stadium(self, db: AsyncSession, schema: StadiumVerificationUpdate, stadium_id: int, user: User):
        """
            Верифицирует стадион.
        """
        stadium = await self.stadium_repository.get_or_404(db=db, object_id=stadium_id)
        self.permission.check_owner_or_admin(current_user=user, model=stadium)
        if stadium.status == StadiumStatus.VERIFICATION:
            raise HTTPException(status_code=400,
                                detail="вы не можете изменить объект, пока у него статус 'На верификации'")

        await self.stadium_repository.update(db=db, model=stadium, schema=schema.model_dump(exclude_unset=True))
        logger.info(f"Cтадион {stadium_id} отправлен на верификацию пользователем {user.id}")
        await self.redis.invalidate_cache(f"stadiums:vendor:{user.id}", f"Обновление стадиона {stadium_id}")
        return Msg(msg=f"Стадион {stadium.id} успешно отправлен на верификацию ")

    @HttpExceptionWrapper
    async def approve_verification_by_admin(self, db: AsyncSession, schema: StadiumVerificationUpdate, stadium_id: int,
                                            user: User):
        """
        Подтверждает верификацию стадиона администратором.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, object_id=stadium_id)
        is_active = schema.status == StadiumStatus.ADDED
        schema.is_active = is_active
        await self.stadium_repository.update(db=db, model=stadium, schema=schema.model_dump(exclude_unset=True))
        logger.info(f"Верификация стадиона {stadium_id} подтверждена администратором {user.id}")
        if schema.is_active:
            await self.redis.invalidate_cache("stadiums:all_active",
                                              f"Кеш для всех активных стадионов инвалидирован из-за подтверждения "
                                              f"верификации стадиона {stadium_id}")
        await self.redis.invalidate_cache(f"stadiums:vendor:{user.id}", f"Обновление стадиона {stadium_id}")
        return Msg(msg=f"Стадиону {stadium.id} присвоен статус {schema.status}")
