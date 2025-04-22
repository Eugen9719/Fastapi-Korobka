from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.interface.base.i_base_repo import ICrudRepository, IReadRepository, IFilterRepository, \
    IPaginateRepository
from backend.app.models import Booking
from backend.app.models.bookings import BookingCreate, BookingUpdate


class IBookingRepository(IReadRepository[Booking], IFilterRepository[Booking], IPaginateRepository[Booking],
                         ICrudRepository[Booking, BookingCreate, BookingUpdate], ABC):

    @abstractmethod
    async def overlapping_booking(self, db: AsyncSession, stadium_id: int, start_time: datetime, end_time: datetime):
        pass

    @abstractmethod
    async def create_with_facilities(self, db: AsyncSession, booking_data: dict,
                                     facilities_data: List[dict]) -> Booking:
        pass

    @abstractmethod
    async def get_booking_from_date(self, db: AsyncSession, stadium_id: int, selected_date: date):
        pass

    @abstractmethod
    async def cancel_booking(self, db: AsyncSession, existing_booking: Booking):
        pass
