import stripe
from typing import List
from fastapi import APIRouter, Query
from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.services import booking_service
from backend.app.models.auth import Msg
from backend.app.models.bookings import BookingCreate, BookingRead, BookingReadGet, PaginatedBookingsResponse
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.config import settings
from backend.core.db import SessionDep
from datetime import  date
stripe.api_key = settings.STRIPE_SECRET_KEY
booking_router = APIRouter()



@booking_router.post('/create', response_model=BookingRead)
@sentry_capture_exceptions
async def create_booking(schema: BookingCreate, db: SessionDep, user: CurrentUser):
    return await booking_service.create_booking(db=db, schema=schema, user=user)



@booking_router.post('/pay/{booking_id}', response_model=dict)
@sentry_capture_exceptions
async def create_payment_session(booking_id: int, db: SessionDep, user: CurrentUser):
    success_url = "http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "http://localhost:8000/cancel"
    payment_url = await booking_service.create_payment_session(db=db, booking_id=booking_id, success_url=success_url,
                                                               cancel_url=cancel_url)
    return {"payment_url": payment_url}



@booking_router.get("/booking_from_date", response_model=List[BookingRead])
@sentry_capture_exceptions
async def booking_from_date(db: SessionDep, stadium_id: int, selected_date: date):
    return await booking_service.get_booking_from_date(db=db, stadium_id=stadium_id, date=selected_date)

@booking_router.get("/bookings-vendor", response_model=PaginatedBookingsResponse)
@sentry_capture_exceptions
async def bookings_vendor(db: SessionDep,user: CurrentUser, page: int = Query(1, ge=1),size: int = Query(2, le=100)):
    return await booking_service.bookings_for_vendor(db, user, page, size)

@booking_router.get("/booking_vendor/{booking_id}", response_model=BookingReadGet)
@sentry_capture_exceptions
async def get_booking(db: SessionDep, booking_id: int, ):
    return await booking_service.get_booking(db=db, booking_id=booking_id)


@booking_router.get('/{stadium_id}/stadium', response_model=List[BookingReadGet])
@sentry_capture_exceptions
async def booking_for_stadium(db: SessionDep, stadium_id: int, user: CurrentUser):
    return await booking_service.booking_stadium(db=db, stadium_id=stadium_id, user=user)


@booking_router.get('/booking_user', response_model=List[BookingReadGet])
@sentry_capture_exceptions
async def booking_for_user(db: SessionDep, user: CurrentUser):
    return await booking_service.get_bookings_user(db, user)




@booking_router.delete("/delete/{booking_id}")
@sentry_capture_exceptions
async def delete_booking(db: SessionDep, current_user: CurrentUser, booking_id: int) -> Msg:
    return await booking_service.delete_booking(db, booking_id=booking_id, user=current_user)


#
# @booking_router.get('/{booking_id}/services', response_model=List[BookingServiceRead])
# @sentry_capture_exceptions
# async def get_booking_services(booking_id: int, db: SessionDep):
#     return await booking_repo.get_booking_services_by_id(db, booking_id)
#
