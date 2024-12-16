import json
import logging
import os

import pytest
from sqlalchemy import create_engine

from sqlmodel import Session, SQLModel
from fastapi.testclient import TestClient
from typing import Generator

from backend.app.models import User, Stadiums, StadiumReview, Booking
from backend.app.models.users import UserCreate
from backend.app.repositories.user_repositories import user_repository
from backend.tests.utils.utils import random_email, random_lower_string, random_username
os.environ["ENVIRONMENT"] = "test"



from backend.core.config import settings

from backend.core.security import get_password_hash
from backend.main import app  # Импортируйте ваше приложение FastAPI


# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def open_json(model: str):
    """Загрузка данных из JSON файла с использованием абсолютного пути."""
    file_path = os.path.join("backend/tests/fixtures/", f"{model}.json")  # Построение пути к файлу в корневой папке
    if not os.path.exists(file_path):
        logger.error(f"Файл {file_path} не найден.")
        raise FileNotFoundError(f"Файл {file_path} не существует")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при загрузке JSON из {file_path}: {e}")
        raise


@pytest.fixture(scope="session")
def test_engine():
    """Создание движка базы данных для тестов."""
    logger.info("Создание тестового движка базы данных.")
    engine = create_engine(settings.database_url)
    return engine


@pytest.fixture(scope="session")
def create_tables(test_engine):
    """Создание и удаление таблиц в базе данных для тестов."""
    if settings.ENVIRONMENT != 'test':
        logger.error("Фикстура create_tables может использоваться только в тестовой среде.")
        raise RuntimeError("Фикстура create_tables может использоваться только в тестовой среде.")

    logger.info("Создание таблиц в тестовой базе данных.")
    SQLModel.metadata.create_all(test_engine)

    yield  # Здесь таблицы созданы, и выполняются тесты

    logger.info("Удаление таблиц из тестовой базы данных.")
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="session")
def db(test_engine, create_tables) -> Generator[Session, None, None]:
    """Сессия базы данных для тестов."""
    logger.info("Создание сессии базы данных для тестов.")
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def prepare_data(db: Session):
    # Очистка данных перед выполнением тестов модуля
    logger.info("Очистка данных из таблиц перед выполнением модуля.")
    for table in reversed(SQLModel.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    """Загрузка данных в базу данных перед тестами в модуле."""
    try:
        # Загрузка пользователей
        users = open_json("user")
        if not users:
            logger.error("Данные пользователей отсутствуют или не загружены.")
        else:
            # logger.info(f"Загруженные пользователи: {users}")
            for user_data in users:
                raw_password = user_data.get("password")
                if not raw_password:
                    raise ValueError(f"Пароль отсутствует для пользователя {user_data.get('email')}")
                user_data["hashed_password"] = get_password_hash(raw_password)
                user_data.pop("password", None)
                user = User(**user_data)
                db.add(user)
            db.commit()
            logger.info(f"Загружено {len(users)} пользователей.")
        stadiums = open_json("stadiums")
        if not stadiums:
            logger.error("Данные полей отсутствуют или не загружены.")
        else:
            for stadiums_data in stadiums:
                stadium = Stadiums(**stadiums_data)
                db.add(stadium)
            db.commit()
            logger.info(f"Загружено {len(stadiums)} полей.")
        reviews = open_json("reviews")
        if not  reviews:
            logger.error("Данные полей отсутствуют или не загружены.")
        else:
            for review_data in reviews:
                review = StadiumReview(**review_data)
                db.add(review)
            db.commit()
            logger.info(f"Загружено {len(reviews)} полей.")
        bookings = open_json("bookings")
        if not bookings:
            logger.error("Данные полей отсутствуют или не загружены.")
        else:
            for booking_data in bookings:
                booking = Booking(**booking_data)
                db.add(booking)
            db.commit()
            logger.info(f"Загружено {len(bookings)} полей.")

    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        db.rollback()
        raise

    yield  # Здесь выполняются тесты


@pytest.fixture(scope='session')
def client() -> Generator[TestClient, None, None]:
    # Создание клиента для тестирования FastAPI-приложения
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def create_user(db: Session):
    def _create_user():
        email = random_email()
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        new_user = user_repository.create(db=db, schema=user_in)
        return new_user, password
    return _create_user

@pytest.fixture()
def create_superuser(create_user, db: Session):
    user, _ = create_user()
    user.is_superuser = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, _
#
#
# @pytest.fixture()
# def create_owner_user(create_user, db: Session):
#     def _create_owner_user():
#         email = random_email()
#         password = random_lower_string()
#         username = random_username()
#         user_in = UserCreate(email=email, password=password, username=username, status="OWNER")
#         new_user = user_crud.user.create_user(db=db, schema=user_in)
#         return new_user, password
#
#     return _create_owner_user
#
#
# @pytest.fixture()
# def create_stadium(db: Session, create_owner_user):
#     user, _ = create_owner_user()
#     schema = StadiumsCreate(
#         name="string",
#         address="string",
#         price=100,
#         country="string",
#         city="string"
#
#     )
#     stadiums = stadium_crud.stadium.create(db=db, schema=schema, owner_id=user.id)
#     return stadiums

# @pytest.fixture(scope="module")
# def upload_directory():
#     upload_dir = "test/test_uploads/"
#     if not os.path.exists(upload_dir):
#         os.makedirs(upload_dir)
#     yield upload_dir
#     shutil.rmtree(upload_dir)
