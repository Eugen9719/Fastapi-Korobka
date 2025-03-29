from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Tuple, Any, Sequence

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateType = TypeVar("CreateType", bound=SQLModel)
UpdateType = TypeVar("UpdateType", bound=SQLModel)


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

class IQueryRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_or_404(self, db: AsyncSession, id: int, options: Optional[list[Any]] = None):
        pass
    @abstractmethod
    async def get_many(self, db: AsyncSession, **kwargs) -> Sequence[ModelType]:
        pass
