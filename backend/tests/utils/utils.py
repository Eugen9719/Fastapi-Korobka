import json
import os
import random
import string
from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.models import User, Stadium, StadiumReview, Booking
from backend.core import security
from backend.core.security import get_password_hash


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_username() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=8))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"



def get_token_header(user_id:int):
    token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {str(token)}"}

def open_json(model: str):
    """Загрузка данных из JSON."""
    file_path = os.path.join("backend/tests/data/", f"{model}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден.")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)




async def load_users(db: AsyncSession):
    users = open_json("user")
    for user_data in users:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        user = User(**user_data)
        db.add(user)
    await db.commit()


async def load_stadiums(db: AsyncSession):
    stadiums = open_json("stadiums")
    for stadium_data in stadiums:
        stadium = Stadium(**stadium_data)
        db.add(stadium)
    await db.commit()

async def load_reviews(db: AsyncSession):
    reviews = open_json("reviews")
    for review_data in reviews:
        review = StadiumReview(**review_data)
        db.add(review)
    await db.commit()

async def load_bookings(db: AsyncSession):
    bookings = open_json("bookings")
    for booking_data in bookings:
        booking_data["start_time"] = datetime.fromisoformat(booking_data["start_time"])
        booking_data["end_time"] = datetime.fromisoformat(booking_data["end_time"])
        booking = Booking(**booking_data)
        db.add(booking)
    await db.commit()
