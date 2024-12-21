from typing import Optional, Generic, TypeVar, Type, Any, Sequence

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Row, RowMapping

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, select


from backend.app.models import User

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateType = TypeVar("CreateType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateType, UpdateType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    @staticmethod
    def save_db(db: Session, db_obj: ModelType) -> ModelType:
        """
        Сохраняет объект в базе данных.
        """
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()  # Откат транзакции в случае ошибки
            raise Exception(f"Ошибка при сохранении объекта: {e}")

    def get_or_404(self, db: Session, id: int) -> ModelType:
        instance = self.get(db=db, id=id)
        if not instance:
            raise HTTPException(status_code=404, detail="Объект не найден")
        return instance


    def exist(self, db: Session, **kwargs) -> bool:
        """
        Проверяет, существует ли запись, соответствующая заданным фильтрам.
        """
        result = db.exec(select(self.model).filter_by(**kwargs)).first()
        return result is not None

    def get(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        Получает объект по заданным параметрам фильтрации.
        """
        return db.exec(select(self.model).filter_by(**kwargs)).first()

    def get_by_filter(self, db: Session, *filters) -> Optional[ModelType]:
        return db.exec(select(self.model).filter(*filters)).first()

    def get_all(self, db: Session, **kwargs) -> Sequence[Row[Any] | RowMapping | Any]:
        """
        Получает список объектов, отфильтрованный по заданным параметрам.
        """
        query = select(self.model)
        if kwargs:
            query = query.filter_by(**kwargs)
        return db.execute(query).scalars().all()

    def get_many(self, db: Session, **kwargs) -> Sequence[ModelType]:
        """
        Получает список объектов по заданным параметрам фильтрации.
        """
        return db.exec(select(self.model).filter_by(**kwargs)).all()

    def all(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """
        Получает все объекты с поддержкой пагинации.
        """
        return db.exec(select(self.model).offset(skip).limit(limit)).all()

    def create(self, db: Session, schema: CreateType, **kwargs) -> ModelType:
        """
        Создает новый объект в базе данных.
        """
        obj_data = jsonable_encoder(schema)
        db_obj = self.model(**obj_data, **kwargs)
        return self.save_db(db, db_obj)

    def update(self, db: Session, model: ModelType, schema: UpdateType) -> ModelType:
        """
        Обновляет существующий объект в базе данных.
        """
        obj_data = schema.model_dump(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(model, key, value)
        return self.save_db(db, model)

    def remove(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        Удаляет объект из базы данных.
        """
        obj = self.get(db, **kwargs)
        if obj:
            try:
                db.delete(obj)
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()  # Откат транзакции в случае ошибки
                raise Exception(f"Ошибка при удалении объекта: {e}")
        return obj

    def check_current_user_or_admin(self,  current_user: User, model: ModelType) -> None:
        if not current_user.is_superuser and model.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Только админ или создатель могут проводить операции")

    def check_current_user(self,  current_user: User, model: ModelType) -> None:
        if not current_user.is_superuser and model.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Вы не можете проводить эту операцию")

