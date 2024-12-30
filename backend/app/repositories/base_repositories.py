from typing import Generic, Type, TypeVar, Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateType = TypeVar("CreateType", bound=SQLModel)
UpdateType = TypeVar("UpdateType", bound=SQLModel)


class AsyncBaseRepository(Generic[ModelType, CreateType, UpdateType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    @staticmethod
    async def save_db(db: AsyncSession, db_obj: ModelType) -> ModelType:
        """
        Сохраняет объект в базе данных.
        """
        try:
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise Exception(f"Ошибка при сохранении объекта: {e}")

    async def get_or_404(self, db: AsyncSession, id: int) -> ModelType:
        instance = await self.get(db=db, id=id)
        if not instance:
            raise HTTPException(status_code=404, detail="Объект не найден")
        return instance

    async def exist(self, db: AsyncSession, **kwargs) -> bool:
        """
        Проверяет, существует ли запись, соответствующая заданным фильтрам.
        """
        result = await db.execute(select(self.model).filter_by(**kwargs))
        return result.scalar() is not None

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """
        Получает объект по заданным параметрам фильтрации.
        """
        result = await db.execute(select(self.model).filter_by(**kwargs))
        return result.scalar_one_or_none()

    async def get_by_filter(self, db: AsyncSession, *filters) -> Optional[ModelType]:
        """
        Получает объект по сложным фильтрам.
        """
        result = await db.execute(select(self.model).filter(*filters))
        return result.scalar()

    async def get_many(self, db: AsyncSession, **kwargs) -> Sequence[ModelType]:
        """
        Получает список объектов по заданным параметрам фильтрации.
        """
        result = await db.execute(select(self.model).filter_by(**kwargs))
        return result.scalars().all()

    async def create(self, db: AsyncSession, schema: CreateType, **kwargs) -> ModelType:
        """
        Создает новый объект в базе данных.
        """
        obj_data = jsonable_encoder(schema)
        db_obj = self.model(**obj_data, **kwargs)
        return await self.save_db(db, db_obj)

    async def update(self, db: AsyncSession, model: ModelType, schema: UpdateType) -> ModelType:
        """
        Обновляет существующий объект в базе данных.
        """
        obj_data = schema.model_dump(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(model, key, value)
        return await self.save_db(db, model)

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

    @classmethod
    def check_current_user_or_admin(cls, current_user, model: ModelType) -> bool:
        """
        Проверяет, является ли пользователь администратором или создателем объекта.
        """
        if not current_user.is_superuser and model.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Только админ или создатель могут проводить операции")
        return True

    @classmethod
    def check_current_user(cls, current_user, model: ModelType) -> None:
        """
        Проверяет, что текущий пользователь является создателем объекта.
        """
        if not current_user.is_superuser and model.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Вы не можете проводить эту операцию")

    # def get_all(self, db: Session, **kwargs) -> Sequence[Row[Any] | RowMapping | Any]:
    #     """
    #     Получает список объектов, отфильтрованный по заданным параметрам.
    #     """
    #     query = select(self.model)
    #     if kwargs:
    #         query = query.filter_by(**kwargs)
    #     return db.execute(query).scalars().all()

    # def all(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
    #     """
    #     Получает все объекты с поддержкой пагинации.
    #     """
    #     return db.exec(select(self.model).offset(skip).limit(limit)).all()
