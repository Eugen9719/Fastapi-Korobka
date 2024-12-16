from fastapi import APIRouter

from backend.app.api.add_reviews_api import add_review_router
from backend.app.api.auth_api import auth_router
from backend.app.api.bookings_api import booking_router
from backend.app.api.stadiums_api import stadium_router

from backend.app.api.user_api import user_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["login"])
api_router.include_router(user_router, prefix="/user", tags=["user"])
api_router.include_router(stadium_router, prefix="/stadium", tags=["stadiums"])
api_router.include_router(booking_router, prefix="/booking", tags=["bookings"])
api_router.include_router(add_review_router,  tags=["reviews"])

