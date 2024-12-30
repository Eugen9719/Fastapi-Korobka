import asyncio
import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator

import pytest

from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlmodel import SQLModel

from backend.app.models import User, Stadiums, StadiumReview, Booking
from backend.app.models.users import UserCreate
from backend.app.repositories.user_repositories import user_repo
from backend.tests.utils.utils import random_email, random_lower_string, random_username


os.environ["ENVIRONMENT"] = "test"
from backend.main import app

from backend.core.config import settings

from backend.core.security import get_password_hash

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


def open_json(model: str):
    """Загрузка данных из JSON."""
    file_path = os.path.join("backend/tests/fixtures/", f"{model}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден.")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


@pytest.fixture(scope="session")
async def test_engine():
    """Асинхронный движок базы данных."""
    logger.info("Создание тестового движка базы данных.")
    engine = create_async_engine(settings.database_url, echo=False)
    return engine


@pytest.fixture(scope="session")
async def create_tables(test_engine):
    """Создание и удаление таблиц."""
    logger.info("Создание таблиц в тестовой базе данных.")
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    logger.info("Удаление таблиц из тестовой базы данных.")
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="session")
async def db(test_engine, create_tables) -> AsyncSession:
    """Асинхронная сессия базы данных."""
    logger.info("Создание сессии базы данных для тестов.")
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def prepare_data(db: AsyncSession):
    """Подготовка данных перед тестами."""
    for table in reversed(SQLModel.metadata.sorted_tables):
        await db.execute(table.delete())
    await db.commit()

    users = open_json("user")
    for user_data in users:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        user = User(**user_data)
        db.add(user)
    await db.commit()
    logger.info(f"Загружено {len(users)} полей.")

    stadiums = open_json("stadiums")
    for stadium_data in stadiums:
        stadium = Stadiums(**stadium_data)
        db.add(stadium)

    await db.commit()  # Подтверждение добавления стадионов
    logger.info(f"Загружено {len(stadiums)} полей.")

    # Загрузка отзывов
    reviews = open_json("reviews")
    for review_data in reviews:
        review = StadiumReview(**review_data)
        db.add(review)

    await db.commit()  # Подтверждение добавления отзывов
    logger.info(f"Загружено {len(reviews)} отзывов.")

    # Загрузка бронирований
    bookings = open_json("bookings")
    for booking_data in bookings:
        booking_data["start_time"] = datetime.fromisoformat(booking_data["start_time"])
        booking_data["end_time"] = datetime.fromisoformat(booking_data["end_time"])
        booking = Booking(**booking_data)
        db.add(booking)

    await db.commit()  # Подтверждение добавления бронирований
    logger.info(f"Загружено {len(bookings)} бронирований.")

    yield


@pytest.fixture(scope="function")
async def client() -> AsyncClient:
    """Асинхронный тестовый клиент для FastAPI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture()
async def create_user(db: AsyncSession):
    async def _create_user():
        email = random_email()
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        new_user = await user_repo.create(db=db, schema=user_in)
        return new_user, password

    return _create_user


@pytest.fixture()
async def create_superuser(create_user, db: AsyncSession):
    user, _ = await create_user()
    user.is_superuser = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, _

# Загрузка стадионов
# stadiums = open_json("stadiums")
# if not stadiums:
#     logger.error("Данные полей отсутствуют или не загружены.")
# else:
#     for stadium_data in stadiums:
#         stadium = Stadiums(**stadium_data)
#         db.add(stadium)
#
#     await db.commit()  # Подтверждение добавления стадионов
#     logger.info(f"Загружено {len(stadiums)} полей.")
#
# # Загрузка отзывов
# reviews = open_json("reviews")
# if not reviews:
#     logger.error("Данные отзывов отсутствуют или не загружены.")
# else:
#     for review_data in reviews:
#         review = StadiumReview(**review_data)
#         db.add(review)
#
#     await db.commit()  # Подтверждение добавления отзывов
#     logger.info(f"Загружено {len(reviews)} отзывов.")
#
# # Загрузка бронирований
# bookings = open_json("bookings")
# if not bookings:
#     logger.error("Данные бронирований отсутствуют или не загружены.")
# else:
#     for booking_data in bookings:
#         booking = Booking(**booking_data)
#         db.add(booking)
#
#     await db.commit()  # Подтверждение добавления бронирований
#     logger.info(f"Загружено {len(bookings)} бронирований.")
