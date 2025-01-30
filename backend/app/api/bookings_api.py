from datetime import datetime
from typing import List

from fastapi import APIRouter, Form, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import selectinload
from sqlmodel import select

from backend.app.services.auth.permissions import CurrentUser

from ..models.auth import Msg
from ..models.bookings import BookingRead, BookingCreate, BookingUpdate, Booking, BookingReadGet
from ..repositories.bookings_repositories import booking_repo
from ...core.db import SessionDep

booking_router = APIRouter()


@booking_router.post('/create', response_model=BookingRead)
async def create_booking(schema: BookingCreate, db: SessionDep, user: CurrentUser):
        return await booking_repo.create_booking(db=db, schema=schema, user=user)



@booking_router.delete("/delete/{booking_id}")
async def delete_booking(db: SessionDep, current_user: CurrentUser, booking_id: int) -> Msg:
    return await booking_repo.delete_booking(db, booking_id=booking_id, user=current_user)


@booking_router.get('/read', response_model=List[BookingReadGet])
async def read_booking(db: SessionDep, user: CurrentUser):
    result = await db.execute(
        select(Booking)
        .filter(Booking.user_id == user.id)
        .options(selectinload(Booking.stadium))  # загрузка связи с stadium
    )
    return result.scalars().all()



@booking_router.get("/booking_from_date", response_model=List[BookingRead])
async def booking_from_date(db: SessionDep, stadium_id: int, date: str):
    return await booking_repo.get_booking_from_date(db=db, stadium_id=stadium_id, date=date)
