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
        """Сохраняет объект в базе данных"""
        merged_obj = await db.merge(db_obj)
        await db.flush()
        await db.refresh(merged_obj)
        return merged_obj

    async def create(self, db: AsyncSession, schema: CreateType, **kwargs) -> ModelType:
        db_obj = self.model(**schema.model_dump(exclude_unset=True), **kwargs)
        return await self.save_db(db, db_obj)

    async def update(self, db: AsyncSession, model: ModelType, schema: UpdateType | dict) -> ModelType:
        """
        Обновляет существующий объект в базе данных.
        """
        obj_data = schema if isinstance(schema, dict) else schema.model_dump(exclude_none=True)
        for key, value in obj_data.items():
            setattr(model, key, value)
        return await self.save_db(db, model)

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """Получение объекта по параметрам"""
        result = await db.execute(select(self.model).filter_by(**kwargs))
        return result.scalar_one_or_none()


    async def remove(self, db: AsyncSession, **kwargs) -> Tuple[bool, Optional[ModelType]]:
        """
        Удаляет объект из базы данных.
        """
        obj = await self.get(db, **kwargs)
        if obj:
            await db.delete(obj)
            await db.flush()
            return True, obj
        return False, None
