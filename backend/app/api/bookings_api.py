from typing import List

from fastapi import APIRouter, HTTPException

from ..base.auth.permissions import CurrentUser
from ..base.utils.deps import SessionDep
from ..models.auth import Msg
from ..models.bookings import BookingRead, BookingCreate, BookingUpdate
from ..repositories.bookings_repositories import booking_repo

booking_router = APIRouter()


@booking_router.post('/create', response_model=BookingRead)
def create_booking(schema: BookingCreate, db: SessionDep, user: CurrentUser):
    return booking_repo.create_booking(db=db, schema=schema, user=user)

@booking_router.put('/update/{booking_id}', response_model=BookingRead)
def update_booking(schema: BookingUpdate, booking_id: int, db: SessionDep, current_user: CurrentUser):
    updated_booking = booking_repo.update_booking(db=db, booking_id=booking_id,schema=schema,  user=current_user)
    return updated_booking

@booking_router.delete("/delete/{booking_id}")
def delete_booking(db: SessionDep, current_user: CurrentUser, booking_id: int) -> Msg:
    booking = booking_repo.get_or_404(db, id=booking_id)
    booking_repo.check_current_user_or_admin(current_user=current_user, model=booking)
    booking_repo.remove(db, id=booking.id)
    return Msg(msg="booking deleted successfully")


@booking_router.get('/read', response_model=List[BookingRead])
def read_booking(db: SessionDep, user: CurrentUser):
    """ bookings for current user"""
    return booking_repo.get_many(db=db, user_id=user.id)

@booking_router.get("/booking_from_date", response_model=List[BookingRead])
def booking_from_date(db: SessionDep, stadium_id: int, date: str):
    bookings = booking_repo.get_booking_from_date(db=db, stadium_id=stadium_id, date=date)
    return bookings