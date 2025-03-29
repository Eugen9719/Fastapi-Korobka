from backend.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from typing import Callable, AsyncGenerator, Annotated
from fastapi import Depends
from loguru import logger


database_url = settings.database_url
engine: AsyncEngine = create_async_engine(database_url, echo=False)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class DatabaseSessionManager:
    """
    Класс для управления асинхронными сессиями базы данных, включая поддержку транзакций и зависимости FastAPI.
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Создаёт и предоставляет новую сессию базы данных.
        Гарантирует закрытие сессии по завершении работы.
        """
        async with self.session_maker() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Ошибка при создании сессии базы данных: {e}")
                raise
            finally:
                await session.close()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Зависимость для FastAPI, возвращающая сессию без управления транзакцией.
        """
        async with self.create_session() as session:
            yield session



    @property
    def session_dependency(self) -> Callable:
        """Возвращает зависимость для FastAPI, обеспечивающую доступ к сессии без транзакции."""
        return Depends(self.get_session)




# Инициализация менеджера сессий базы данных
session_manager = DatabaseSessionManager(async_session_maker)

# Зависимости FastAPI для использования сессий
SessionDep = Annotated[AsyncSession, session_manager.session_dependency]



