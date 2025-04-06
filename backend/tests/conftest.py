import asyncio

import logging
import os
from typing import AsyncGenerator, Any
from unittest.mock import AsyncMock

import pytest

from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlmodel import SQLModel

from backend.app.dependencies.services import redis_client
from backend.tests.utils.utils import load_users, load_stadiums, load_reviews, load_bookings

from backend.core.config import settings

os.environ["ENVIRONMENT"] = "test"
from backend.main import app

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для сессии."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()





@pytest.fixture(scope="session")
async def test_engine():
    """Создание движка БД на сессию тестов"""
    engine = create_async_engine(settings.database_url, echo=False)
    yield engine
    await engine.dispose()  # Важно: закрыть движок после завершения тестов.


@pytest.fixture(scope="session", autouse=True)
async def create_tables(test_engine):
    """Создание таблиц перед тестами и удаление после"""
    logger.info("Создание таблиц в тестовой базе данных.")
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield  # Тесты выполняются здесь
    logger.info("Удаление таблиц из тестовой базы данных.")
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="class")
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД (изолированной на уровне теста)"""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()  # Явное закрытие сессии


@pytest.fixture(scope="class")
async def test_data(db: AsyncSession):
    # Загрузка тестовых данных
    logger.info("Загрузка тестовых данных")
    try:
        await load_users(db)
        logger.info('Загружены тестовые данные пользователей')
        await load_stadiums(db)
        logger.info('Загружены тестовые данные стадионов')
        await load_reviews(db)
        logger.info('Загружены тестовые данные отзывов')
        await load_bookings(db)
        logger.info('Загружены тестовые данные бронирования')



    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка загрузки тестовых данных: {e}")
        raise

    yield

    logger.info("Очистка тестовых данных после модуля")
    logger.info(f"Сброс sequence: ")
    try:
        # Удаляем все записи
        for table in reversed(SQLModel.metadata.sorted_tables):
            await db.execute(table.delete())

        # Сбрасываем автоинкрементные последовательности
        for table in SQLModel.metadata.sorted_tables:
            table_name = table.name
            sequence_name = f"{table_name}_id_seq"
            try:
                await db.execute(text(f'ALTER SEQUENCE "{sequence_name}" RESTART WITH 1'))

            except Exception as e:
                logger.warning(f"Не удалось сбросить sequence {sequence_name}: {e}")

        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при очистке тестовых данных: {e}")



@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, Any]:
    """Асинхронный тестовый клиент для FastAPI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    async_mock = AsyncMock()
    async_mock.fetch_cached_data.return_value = None
    async_mock.cache_data.return_value = None
    async_mock.delete_cache_by_prefix.return_value = None
    async_mock.invalidate_cache = AsyncMock(return_value=None)

    monkeypatch.setattr(redis_client, "get_client", AsyncMock(return_value=async_mock))
    monkeypatch.setattr(redis_client, "fetch_cached_data", async_mock.fetch_cached_data)
    monkeypatch.setattr(redis_client, "cache_data", async_mock.cache_data)
    monkeypatch.setattr(redis_client, "delete_cache_by_prefix", async_mock.delete_cache_by_prefix)
    monkeypatch.setattr(redis_client, "invalidate_cache", async_mock.invalidate_cache)

    return async_mock  # Возвращаем мок для проверок


