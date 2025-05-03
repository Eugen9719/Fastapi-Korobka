import logging
from fastapi import HTTPException, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.interface.utils.i_image_handler import ImageHandler
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User
from backend.app.models.stadiums import StadiumStatus
from backend.app.services.utils_service.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.redis import RedisClient

logger = logging.getLogger(__name__)


class StadiumImageService:
    """Сервис управления стадионом"""

    def __init__(self, stadium_repository: IStadiumRepository, permission: PermissionService, redis: RedisClient,
                 image_handler: ImageHandler,
                 ):
        self.stadium_repository = stadium_repository
        self.permission = permission
        self.redis = redis
        self.image_handler = image_handler


    @HttpExceptionWrapper
    async def upload_image(self, db: AsyncSession, stadium_id: int, user: User, file: UploadFile = File(...)):
        """
        Загружает изображение для стадиона.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, object_id=stadium_id)
        if stadium.status == StadiumStatus.VERIFICATION:
            raise HTTPException(status_code=400,
                                detail="вы не можете изменить объект, пока у него статус 'На верификации")
        was_active = stadium.is_active

        await self.image_handler.delete_old_image(db, stadium)
        image = await self.image_handler.upload_image(db=db, instance=stadium, file=file)
        logger.info(f"Изображение загружено для стадиона {stadium_id}")

        if was_active and not stadium.is_active:
            await self.redis.invalidate_cache("stadiums:all_active",
                                              f"Загрузка изображения для стадиона {stadium_id}")
        await self.redis.invalidate_cache(f"stadiums:vendor:{user.id}", f"Обновление стадиона {stadium_id}")

        return image

