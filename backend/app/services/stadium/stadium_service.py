import logging
from datetime import datetime
from typing import List

import sentry_sdk
from fastapi import HTTPException, UploadFile, File
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


from backend.app.interface.utils.i_image_handler import ImageHandler
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User
from backend.app.models.additional_facility import StadiumFacilityDelete

from backend.app.models.auth import Msg
from backend.app.models.base_model_public import AdditionalFacilityReadBase
from backend.app.models.stadium_reviews import StadiumReview

from backend.app.models.stadiums import  StadiumStatus, StadiumCreate, StadiumsUpdate, \
    StadiumsRead, Stadium, StadiumsReadWithFacility, StadiumFacilityCreate, PaginatedStadiumsResponse, PriceInterval, \
    StadiumCreateWithInterval, PriceIntervalCreate

from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.redis import RedisClient

logger = logging.getLogger(__name__)


class StadiumService:
    """Сервис управления стадионом"""

    def __init__(self, stadium_repository: IStadiumRepository, permission: PermissionService, redis: RedisClient,
                 image_handler: ImageHandler,
                 ):
        self.stadium_repository = stadium_repository
        self.permission = permission
        self.redis = redis
        self.image_handler = image_handler

    @HttpExceptionWrapper
    async def create_stadium(self, db: AsyncSession, schema: StadiumCreateWithInterval, user: User):
        """Создание стадиона"""

        # Проверка уникальности слага
        if not await self.stadium_repository.is_slug_unique(db, schema.slug):
            logger.info(f"Слаг используется: {schema.slug} пользователем {user.id}")
            raise HTTPException(status_code=400, detail="Слаг уже используется")

        # Создаем стадион (без интервалов)
        stadium_data = schema.model_dump(exclude={"price_intervals"})
        new_stadium = await self.stadium_repository.create(
            db=db,
            schema=StadiumCreate(**stadium_data),
            user_id=user.id
        )

        # Если price_intervals не пустой, добавляем интервалы
        if schema.price_intervals:
            await self.stadium_repository.add_price_intervals(db, schema.price_intervals, new_stadium.id)

        return new_stadium

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

    @HttpExceptionWrapper
    async def update_stadium(self, db: AsyncSession, schema: StadiumsUpdate, stadium_id: int, user: User):
        """
        Обновляет данные стадиона.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
        self.permission.check_owner_or_admin(current_user=user, model=stadium)
        if stadium.status == StadiumStatus.VERIFICATION:
            raise HTTPException(status_code=400,
                                detail="вы не можете изменить объект, пока у него статус 'На верификации'")

        if stadium.slug != schema.slug and not await self.stadium_repository.is_slug_unique(db, schema.slug):
            logger.info(f"Слаг '{schema.slug}' уже используется пользователем {user.id}")
            sentry_sdk.capture_message(f"Слаг '{schema.slug}' уже используется пользователем {user.id}",
                                       level="warning")
            raise HTTPException(status_code=400, detail="Слаг уже используется")

        was_active = stadium.is_active
        stadium = await self.stadium_repository.update(db=db, model=stadium, schema=schema)
        logger.info(f"Стадион {stadium_id} обновлен пользователем {user.id}", )

        if was_active and not stadium.is_active:
            await self.redis.invalidate_cache("stadiums:all_active", f"Деактивация стадиона {stadium_id}")
        await self.redis.invalidate_cache(f"stadiums:vendor:{user.id}", f"Обновление стадиона {stadium_id}")

        return stadium

    @HttpExceptionWrapper
    async def delete_stadium(self, db: AsyncSession, user: User, stadium_id: int):
        """
        Удаляет стадион.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
        self.permission.check_owner_or_admin(current_user=user, model=stadium)

        was_active = stadium.is_active
        await self.stadium_repository.remove(db=db, id=stadium.id)
        if was_active:
            await self.redis.invalidate_cache("stadiums:all_active", f"Удаление стадиона {stadium_id}")
        logger.info(f"Стадион {stadium_id} удален пользователем {user.id}")
        return Msg(msg="Стадион удален успешно")

    @HttpExceptionWrapper
    async def upload_image(self, db: AsyncSession, stadium_id: int, user: User, file: UploadFile = File(...)):
        """
        Загружает изображение для стадиона.
        """

        stadium = await self.stadium_repository.get_or_404(db=db, id=stadium_id)
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

    @HttpExceptionWrapper
    async def get_stadiums(self, db: AsyncSession, ):
        """
        **Описание:**
        Получает список всех активных стадионов из базы данных.

        """
        # Кеш для всех активных стадионов
        cache_key = "stadiums:all_active"

        # Проверяем, есть ли данные в кеше
        cached_stadiums = await self.redis.fetch_cached_data(cache_key=cache_key, schema=StadiumsRead)
        if cached_stadiums:
            return cached_stadiums["items"]  # Возвращаем данные из кеша

        # Если данных нет в кеше, получаем их из базы данных
        stadiums = await self.stadium_repository.get_many(db=db, is_active=True)

        # Подготавливаем данные для кеширования
        json_data = {"items": [stadium.model_dump() for stadium in stadiums]}
        await self.redis.cache_data(cache_key, json_data)  # Кешируем данные

        # Возвращаем данные в формате, ожидаемом в response_model
        return [StadiumsRead(**stadium.model_dump()) for stadium in stadiums]

    @HttpExceptionWrapper
    async def get_vendor_stadiums(self, db: AsyncSession, user: User, page: int,
                                  size: int) -> PaginatedStadiumsResponse:
        # Кеш для стадионов вендора с пагинацией
        cache_key = f"stadiums:vendor:{user.id}:page{page}:size{size}"

        # Пытаемся получить данные из кеша
        cached_data = await self.redis.fetch_cached_data(cache_key=cache_key, schema=Stadium)
        if cached_data:
            return PaginatedStadiumsResponse(**cached_data)

        # Если данных нет в кеше, получаем их из базы данных
        query = select(Stadium).where(Stadium.user_id == user.id)
        paginated_data = await self.stadium_repository.paginate(query, db, page, size)

        # Подготавливаем данные для кеширования
        json_data = {
            "items": [stadium.model_dump() for stadium in paginated_data["items"]],
            "page": paginated_data["page"],
            "pages": paginated_data["pages"]
        }
        await self.redis.cache_data(cache_key, json_data)

        # Возвращаем данные в формате, ожидаемом в response_model
        return PaginatedStadiumsResponse(**paginated_data)

    @HttpExceptionWrapper
    async def detail_stadium(self, db: AsyncSession, stadium_id: int):
        # Получаем стадион с загруженными связями
        stadium = await self.stadium_repository.get_or_404(
            db=db,
            id=stadium_id,
            options=[
                selectinload(Stadium.stadium_reviews).selectinload(StadiumReview.user_review),
                selectinload(Stadium.stadium_facility)
            ]
        )

        # Формируем список услуг из уже загруженной связи
        facility_response = [
            AdditionalFacilityReadBase(
                id=facility.id,
                name=facility.name,
                svg_image=facility.svg_image,
                description=facility.description,
                price=facility.price
            )
            for facility in stadium.stadium_facility  # Используем уже загруженные данные
        ]

        # Создаем объект StadiumsReadWithServices
        stadium_with_facility = StadiumsReadWithFacility.model_validate(stadium).model_copy(
            update={"stadium_facility": facility_response})

        return stadium_with_facility

    @HttpExceptionWrapper
    async def add_facility_stadium(self, db: AsyncSession, stadium_id: int,
                                   facility_schema: List[StadiumFacilityCreate], user: User):

        stadium = await self.stadium_repository.get_or_404(db, id=stadium_id)
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
    async def delete_facility_from_stadium(self, db: AsyncSession, schema: StadiumFacilityDelete, user: User) -> dict:
        """
        Удаляет связь сервиса со стадионом.
        """

        # 1. Проверка прав доступа
        stadium = await self.stadium_repository.get_or_404(db, id=schema.stadium_id)
        self.permission.check_owner_or_admin(user, stadium)

        # 2. Поиск и удаление связи в одной операции
        delete_result = await self.stadium_repository.delete_service(db, schema)

        if not delete_result.scalar_one_or_none():
            raise HTTPException(404, "Связь сервиса со стадионом не найдена")

        # 3. Инвалидация кеша (перед коммитом для атомарности)
        await self.redis.delete_cache_by_prefix(f"stadium:{schema.stadium_id}:")

        logger.info(
            f"Удален сервис {schema.facility_id} со стадиона {schema.stadium_id} "
            f"пользователем {user.id}"
        )

        return {
            "status": "success",
            "message": "Связь сервиса со стадионом успешно удалена"
        }

    @HttpExceptionWrapper
    async def get_available_stadiums(self, db: AsyncSession, city: str, start_time: datetime, end_time: datetime) -> \
            List[StadiumsRead]:
        pass
        # return  await  self.stadium_repository.search_available_stadiums(db, city, start_time, end_time)
