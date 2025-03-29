import logging
from typing import Optional, Sequence, Tuple, Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from backend.app.abstractions.repository import IQueryRepository, ModelType, ICrudRepository, CreateType, UpdateType


logger = logging.getLogger(__name__)





# Миксин для дополнительных операций
class QueryMixin(IQueryRepository[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_or_404(self, db: AsyncSession, id: int, options: Optional[list[Any]] = None):
        query = select(self.model).where(id == self.model.id)
        if options:
            query = query.options(*options)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()  # Возвращает первый результат (или None)

        if not instance:
            raise HTTPException(status_code=404, detail="Объект не найден")

        return instance

    async def get_many(self, db: AsyncSession, **kwargs) -> Sequence[ModelType]:
        """
        Простой поиск по точным совпадениям полей.
        Пример: await get_many(db, status='active', is_verified=True)
        """
        result = await db.execute(select(self.model).filter_by(**kwargs))

        return result.scalars().all()

    async def exist(self, db: AsyncSession, **kwargs) -> bool:
        """
        Проверяет, существует ли запись, соответствующая заданным фильтрам.
        """
        result = await db.execute(select(self.model).filter_by(**kwargs))
        return result.scalar() is not None

    async def base_filter(self, db: AsyncSession, *filters, options=None):
        """
        Расширенный поиск с поддержкой сложных условий и eager loading.
        Пример: await base_filter(db, User.age > 18, options=[joinedload(...)])
        """
        query = select(self.model).where(*filters)

        if options:
            query = query.options(*options)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def paginate(query, db: AsyncSession, page: int, size: int):
        offset = (page - 1) * size

        # Подсчет количества записей
        total_query = select(func.count()).select_from(query)
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # Получаем записи с пагинацией
        result = await db.execute(query.offset(offset).limit(size))
        items = result.scalars().all()

        pages = (total + size - 1) // size if total else 1

        return {
            "items": items,
            "page": page,
            "pages": pages
        }


class AsyncBaseRepository(ICrudRepository[ModelType, CreateType, UpdateType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    @staticmethod
    async def save_db(db: AsyncSession, db_obj: ModelType) -> ModelType:
        """
        Сохраняет объект в базе данных.
            db: Асинхронная сессия SQLAlchemy
            db_obj: Объект модели для сохранения
        """
        try:
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise e

    async def create(self, db: AsyncSession, schema: CreateType, **kwargs) -> ModelType:
        """
        Создает новый объект в базе данных.
        """
        try:
            data = schema.model_dump(exclude_unset=True)
            logger.info(f"Создание объекта {self.model.__name__} с данными: {data}, доп. параметры: {kwargs}")

            db_obj = self.model(**data, **kwargs)
            saved_obj = await self.save_db(db, db_obj)

            logger.info(f"Объект {self.model.__name__} создан: id={saved_obj.id}")

            return saved_obj

        except Exception as e:
            logger.error(f"Create error: {e}")
            raise HTTPException(status_code=400, detail="Ошибка при создании объекта")

    async def update(self, db: AsyncSession, model: ModelType, schema: UpdateType | dict) -> ModelType:
        """
        Обновляет существующий объект в базе данных.
        """
        try:
            obj_data = schema if isinstance(schema, dict) else schema.model_dump(exclude_none=True)
            for key, value in obj_data.items():
                setattr(model, key, value)
            return await self.save_db(db, model)
        except Exception as e:
            logger.error(f'Ошибка при обновлении: {e}')
            raise HTTPException(status_code=400, detail="Ошибка при обновлении объекта")

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """Получение объекта по параметрам"""
        try:
            result = await db.execute(select(self.model).filter_by(**kwargs))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка: {e}")
            raise HTTPException(status_code=500, detail="Ошибка получения объекта")

    async def remove(self, db: AsyncSession, **kwargs) -> Tuple[bool, Optional[ModelType]]:
        """
        Удаляет объект из базы данных.
        """
        obj = await self.get(db, **kwargs)
        if obj:
            try:
                await db.delete(obj)
                await db.commit()
                return True, obj
            except SQLAlchemyError as e:
                await db.rollback()
                raise Exception(f"Ошибка при удалении объекта: {e}")
        return False, None





