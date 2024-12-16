from datetime import datetime
from decimal import Decimal

from .base_repositories import BaseRepository
from sqlmodel import Session, select, func
from fastapi import HTTPException

from .stadiums_repositories import stadium_repo
from ..models import User
from ..models.stadiums import Stadiums
from ..models.bookings import Booking, BookingCreate, BookingUpdate


class BookingRepositories(BaseRepository[Booking, BookingCreate, BookingUpdate]):
    @staticmethod
    def _check_overlapping_booking(db: Session, stadium_id: int, start_time: datetime, end_time: datetime):
        overlapping_booking = db.execute(
            select(Booking).where(
                Booking.stadium_id == stadium_id,
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        ).scalar()  # Проверяем только первое пересечение

        if overlapping_booking:
            raise HTTPException(status_code=400, detail="The selected time is already booked.")

    @staticmethod
    def _calculate_price(price_per_hour: Decimal, start_time: datetime, end_time: datetime) -> float:
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="End time must be greater than start time.")

        duration = Decimal((end_time - start_time).total_seconds()) / Decimal(3600)  # Время в часах
        return float(duration * price_per_hour)

    def create_booking(self, db: Session, schema: BookingCreate, user: User):
        # Проверяем пересечения бронирований
        self._check_overlapping_booking(db, schema.stadium_id, schema.start_time, schema.end_time)

        # Получаем стадион
        stadium = stadium_repo.get_or_404(db=db, id=schema.stadium_id)
        if not stadium.is_active:
            raise HTTPException(status_code=400, detail="The stadium is not active for booking.")

        # Считаем цену бронирования
        booking_price = self._calculate_price(stadium.price, schema.start_time, schema.end_time)

        # Создаем бронирование через базовый метод
        return super().create(db=db, schema=schema, user_id=user.id, price=booking_price, )

    def update_booking(self, db: Session, booking_id: int, schema: BookingUpdate, user: User):
        bookings = self.get(db, id=booking_id)
        if not bookings:
            raise HTTPException(status_code=404, detail="Booking not found.")

        if bookings.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this booking.")

        # Определяем новые значения стадиона и времени
        new_stadium_id = schema.stadium_id or bookings.stadium_id
        new_start_time = schema.start_time or bookings.start_time
        new_end_time = schema.end_time or bookings.end_time

        # Проверяем, изменились ли стадион или время
        if (
                new_stadium_id != bookings.stadium_id or
                new_start_time != bookings.start_time or
                new_end_time != bookings.end_time
        ):
            # Проверяем на пересечение с другими букингами
            self._check_overlapping_booking(db, new_stadium_id, new_start_time, new_end_time)

            # Получаем стадион для пересчета цены
            stadium = db.execute(select(Stadiums).where(Stadiums.id == new_stadium_id)).first()
            if not stadium:
                raise HTTPException(status_code=404, detail="Stadium not found.")

            # Пересчитываем цену
            bookings.price = self._calculate_price(stadium.price, new_start_time, new_end_time)

        # Обновляем поля букинга
        return self.update(db, bookings, schema)

    def get_booking_from_date(self, db: Session, stadium_id: int, date: str):
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()

        return db.exec(select(self.model).where(self.model.stadium_id == stadium_id,
                                                func.date(self.model.start_time) == selected_date
                                                )).scalars()


booking_repo = BookingRepositories(Booking)
