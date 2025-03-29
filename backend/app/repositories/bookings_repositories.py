from datetime import datetime, date
from typing import List

from sqlalchemy import delete

from .base_repositories import AsyncBaseRepository, QueryMixin
from sqlmodel import select, func
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.bookings import Booking, BookingCreate, BookingUpdate, BookingFacility
from ..services import booking
from ..services.booking.booking_service import BookingService


class BookingRepository(AsyncBaseRepository[Booking, BookingCreate, BookingUpdate], QueryMixin):
    def __init__(self):
        super().__init__(Booking)

    @staticmethod
    async def overlapping_booking(db: AsyncSession, stadium_id: int, start_time: datetime, end_time: datetime):
        result =  await db.execute(
            select(Booking).where(
                Booking.stadium_id == stadium_id,
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_with_facilities(db: AsyncSession,booking_data: dict,facilities_data: List[dict]) -> Booking:
        try:
            # Создаем бронирование
            booking = Booking(**booking_data)
            db.add(booking)
            await db.flush()

            # Добавляем услуги
            if facilities_data:
                for item in facilities_data:
                    db.add(BookingFacility(
                        booking_id=booking.id,
                        facility_id=item['facility'].id,
                        quantity=item['quantity'],
                        total_price=item['total']
                    ))

            await db.commit()
            await db.refresh(booking)
            return booking

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Booking creation failed: {str(e)}"
            )




    async def get_booking_from_date(self, db: AsyncSession, stadium_id: int, selected_date: date):
        result = await db.execute(
            select(self.model).where(
                self.model.stadium_id == stadium_id,
                func.date(self.model.start_time) == selected_date
            )
        )
        return result.scalars().all()

    @staticmethod
    async def cancel_booking(db: AsyncSession, existing_booking: Booking):
        await db.execute(delete(BookingService).where(BookingService.booking_id == existing_booking.id))
        # Удаляем само бронирование
        await db.delete(booking)
        await db.commit()
