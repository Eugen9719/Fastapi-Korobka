import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession


from backend.app.models import Stadiums, StadiumReview, Booking
from backend.app.models.users import User
from backend.core.db import engine

from backend.core.security import get_password_hash
from backend.tests.conftest import open_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def prepare_local_data(db: AsyncSession):
    try:
        # Загрузка пользователей
        users = open_json("user")
        if not users:
            logger.error("Данные пользователей отсутствуют или не загружены.")
        else:
            for user_data in users:
                raw_password = user_data.get("password")
                if not raw_password:
                    raise ValueError(f"Пароль отсутствует для пользователя {user_data.get('email')}")
                user_data["hashed_password"] = get_password_hash(raw_password)
                user_data.pop("password", None)
                user = User(**user_data)
                db.add(user)
            await db.commit()  # Асинхронный commit
            logger.info(f"Загружено {len(users)} пользователей.")

        # # Загрузка стадионов
        # stadiums = open_json("stadiums")
        # if not stadiums:
        #     logger.error("Данные полей отсутствуют или не загружены.")
        # else:
        #     for stadiums_data in stadiums:
        #         stadium = Stadiums(**stadiums_data)
        #         db.add(stadium)
        #     await db.commit()  # Асинхронный commit
        #     logger.info(f"Загружено {len(stadiums)} полей.")
        #
        # # Загрузка отзывов
        # reviews = open_json("reviews")
        # if not reviews:
        #     logger.error("Данные полей отсутствуют или не загружены.")
        # else:
        #     for review_data in reviews:
        #         review = StadiumReview(**review_data)
        #         db.add(review)
        #     await db.commit()  # Асинхронный commit
        #     logger.info(f"Загружено {len(reviews)} полей.")
        #
        # # Загрузка бронирований
        # bookings = open_json("bookings")
        # if not bookings:
        #     logger.error("Данные полей отсутствуют или не загружены.")
        # else:
        #     for booking_data in bookings:
        #         booking = Booking(**booking_data)
        #         db.add(booking)
        #     await db.commit()  # Асинхронный commit
        #     logger.info(f"Загружено {len(bookings)} полей.")

    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        await db.rollback()  # Асинхронный rollback
        raise


async def init() -> None:
    async with AsyncSession(engine) as session:
        await prepare_local_data(session)  # Не забывайте добавлять await

if __name__ == "__main__":
    asyncio.run(init())  # Запуск асинхронной функции

