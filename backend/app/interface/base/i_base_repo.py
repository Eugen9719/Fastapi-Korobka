from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Tuple, Any, Sequence

from pydantic import BaseModel
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateType = TypeVar("CreateType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)




# Базовый доступ (по id и по фильтрам)
class IReadRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_or_404(self, db: AsyncSession, object_id: int, options: Optional[list[Any]] = None) -> ModelType:
        pass

    @abstractmethod
    async def get_many(self, db: AsyncSession, **kwargs) -> Sequence[ModelType]:
        pass

# Расширенная фильтрация
class IFilterRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def base_filter(self, db: AsyncSession, *filters, options=None) -> Sequence[ModelType]:
        pass

# Пагинация
class IPaginateRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def paginate(self, query, db: AsyncSession, page: int, size: int) -> dict:
        pass


# Интерфейс для базовых операций с репозиторием
class ICrudRepository(ABC, Generic[ModelType, CreateType, UpdateType]):
    @abstractmethod
    async def create(self, db: AsyncSession, schema: CreateType, **kwargs) -> ModelType:
        pass
    @abstractmethod
    async def update(self, db: AsyncSession, model: ModelType, schema: UpdateType | dict) -> ModelType:
        pass
    @abstractmethod
    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        pass
    @abstractmethod
    async def remove(self, db: AsyncSession, **kwargs) -> Tuple[bool, Optional[ModelType]]:
        pass

    @abstractmethod
    async def save_db(self, db: AsyncSession, db_obj: ModelType) -> ModelType:
        pass