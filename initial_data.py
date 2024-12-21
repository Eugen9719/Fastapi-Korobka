import logging

from sqlmodel import Session, select

from backend.app.models import Stadiums, StadiumReview, Booking
from backend.app.models.users import User, UserCreateAdmin
from backend.app.repositories.user_repositories import admin_user_repository
from backend.core.config import settings
from backend.core.db import engine
from backend.core.security import get_password_hash
from backend.tests.conftest import open_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# def init_db(db: Session) -> None:
#     user = db.execute(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
#     if not user:
#         user_in = UserCreateAdmin(
#
#             email=settings.FIRST_SUPERUSER,
#             password=settings.FIRST_SUPERUSER_PASSWORD,
#             is_superuser=True,
#             is_active=True,
#         )
#         admin_user_repository.create_user(db=db, schema=user_in)
#         logging.info(f"Суперпользователь с email {settings.FIRST_SUPERUSER} был создан.")
#     else:
#         logging.info(f"Суперпользователь с email {settings.FIRST_SUPERUSER} уже существует.")


def prepare_local_data(db: Session):
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
        if not reviews:
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


def init() -> None:
    with Session(engine) as session:
        prepare_local_data(session)


if __name__ == "__main__":
    init()
