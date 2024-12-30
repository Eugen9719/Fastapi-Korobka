from typing import List

from fastapi import APIRouter

from ..base.auth.permissions import CurrentUser
from ..base.utils.deps import SessionDep
from ..models.auth import Msg
from ..models.bookings import BookingRead, BookingCreate, BookingUpdate
from ..repositories.bookings_repositories import booking_repo

booking_router = APIRouter()


@booking_router.post('/create', response_model=BookingRead)
async def create_booking(schema: BookingCreate, db: SessionDep, user: CurrentUser):
    return await booking_repo.create_booking(db=db, schema=schema, user=user)


@booking_router.put('/update/{booking_id}', response_model=BookingRead)
async def update_booking(schema: BookingUpdate, booking_id: int, db: SessionDep, current_user: CurrentUser):
    return await booking_repo.update_booking(db=db, booking_id=booking_id, schema=schema, user=current_user)


@booking_router.delete("/delete/{booking_id}")
async def delete_booking(db: SessionDep, current_user: CurrentUser, booking_id: int) -> Msg:
    return await booking_repo.delete_booking(db, booking_id=booking_id, user=current_user)


@booking_router.get('/read', response_model=List[BookingRead])
async def read_booking(db: SessionDep, user: CurrentUser):
    return await booking_repo.get_many(db=db, user_id=user.id)


@booking_router.get("/booking_from_date", response_model=List[BookingRead])
async def booking_from_date(db: SessionDep, stadium_id: int, date: str):
    return await booking_repo.get_booking_from_date(db=db, stadium_id=stadium_id, date=date)
