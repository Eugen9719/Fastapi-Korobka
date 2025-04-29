import logging
from datetime import datetime, timedelta
import stripe
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.repositories.i_booking_repo import IBookingRepository
from backend.app.interface.repositories.i_stadium_repo import IStadiumRepository
from backend.app.models import User, Stadium
from backend.app.models.bookings import BookingCreate, StatusBooking, Booking, BookingFacility, \
    PaginatedBookingsResponse
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.services.auth.permission import PermissionService
from backend.app.services.decorators import HttpExceptionWrapper

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BookingService:
    """Сервис управления бронированием"""

    def __init__(self, booking_repository: IBookingRepository, stadium_repository: IStadiumRepository,
                 facility_repository: FacilityRepository,
                 permission: PermissionService):
        self.booking_repository = booking_repository
        self.stadium_repository = stadium_repository
        self.facility_repository = facility_repository
        self.permission = permission

    async def _check_overlapping_booking(self, db: AsyncSession, stadium_id: int, start_time: datetime,
                                         end_time: datetime):
        overlapping_booking = await self.booking_repository.overlapping_booking(db, stadium_id, start_time, end_time)
        if overlapping_booking:
            raise HTTPException(status_code=400, detail="Этот промежуток времени уже забронирован.")

    @staticmethod
    def _calculate_price(stadium: Stadium, start_time: datetime, end_time: datetime):

        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="Время окончания должно быть больше времени начала."
            )

        total = 0
        current = start_time
        day_of_week = start_time.weekday()  # 0=понедельник, 6=воскресенье

        while current < end_time:
            segment_end = min(current + timedelta(minutes=30), end_time)
            segment_start_time = current.time()
            segment_end_time = segment_end.time()

            # Ищем подходящий интервал (сначала для дня недели, потом общий)
            price = None
            for interval in stadium.price_intervals:
                if ((interval.day_of_week == day_of_week or interval.day_of_week is None)
                        and segment_start_time < interval.end_time
                        and segment_end_time > interval.start_time
                ):
                    price = interval.price
                    # Приоритет у интервалов с указанным днём недели
                    if interval.day_of_week == day_of_week:
                        break

            # Если интервал не найден, используем стандартную цену
            if price is None:
                price = stadium.default_price

            total += price
            current = segment_end

            # Обновляем день недели, если текущее время перешло на следующий день
            if segment_end.day > current.day:
                day_of_week = segment_end.weekday()

        return total

    @HttpExceptionWrapper
    async def create_booking(self, db: AsyncSession, schema: BookingCreate, user: User):
        # 1. Проверка пересечений бронирований
        await self._check_overlapping_booking(db, schema.stadium_id, schema.start_time, schema.end_time)

        # 2. Получаем и проверяем стадион

        stadium = await self.stadium_repository.get_or_404(
            db,
            schema.stadium_id,
            options=[selectinload(Stadium.price_intervals)]  # type: ignore
        )

        if not stadium.is_active:
            raise HTTPException(status_code=400, detail="Этот стадион не активен для бронирования")

        # 3. Проверяем услуги
        facilities_data = []
        if schema.list_facility:
            for facility_data in schema.list_facility:
                facility = await self.facility_repository.get_facility(db, facility_data.facility_id)
                if not facility:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Service with ID {facility_data.facility_id} not found"
                    )
                facilities_data.append({
                    'facility': facility,
                    'quantity': facility_data.quantity,
                    'total': facility.price * facility_data.quantity
                })

        # 4. Рассчитываем цену
        booking_price = self._calculate_price(stadium, schema.start_time, schema.end_time)
        total_price = booking_price + sum(item['total'] for item in facilities_data)

        # 5. Подготавливаем данные для создания бронирования
        booking_data = {
            'start_time': schema.start_time,
            'end_time': schema.end_time,
            'stadium_id': schema.stadium_id,
            'user_id': user.id,
            'status': StatusBooking.MANUAL if stadium.user_id == user.id else StatusBooking.PENDING,
            'price_booking': booking_price,
            'total_price': total_price,
            'status_note': schema.status_note
        }

        # 6. Создаем бронирование через репозиторий (включая коммит)
        return await self.booking_repository.create_with_facilities(
            db=db,
            booking_data=booking_data,
            facilities_data=facilities_data
        )

    @HttpExceptionWrapper
    async def create_payment_session(self, db: AsyncSession, booking_id: int, success_url: str, cancel_url: str):
        booking = await self.booking_repository.get_or_404(
            db=db,
            object_id=booking_id,
            options=[selectinload(Booking.stadium),
                     selectinload(Booking.booking_facility).selectinload(BookingFacility.facility)]) # type: ignore

        if booking.status != StatusBooking.PENDING:
            raise HTTPException(status_code=400, detail="Order must be pending to create a payment session.")

        # Формирование списка line_items для Stripe
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Заказ #{booking.id} - {booking.stadium.name}",
                        "description": (
                            f"Бронирование с {booking.start_time} "
                            f"по {booking.end_time}"
                        ),

                    },
                    "unit_amount": int(booking.price_booking * 100),  # Общая стоимость заказа в центах
                },
                "quantity": 1,
            },

        ]
        if booking.booking_facility:
            # Добавление услуг из бронирования
            for facility in booking.booking_facility:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": facility.facility.name,  # Имя услуги
                            "description": facility.facility.description or "Описание услуги",
                            "images": ["https://example.com/image2.png"],
                        },
                        "unit_amount": int(facility.facility.price * 100),
                    },
                    "quantity": facility.quantity,
                })

        # Создание Stripe-сессии
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"booking_id": booking.id},  # Метаданные для связи заказа со Stripe
        )

        return session.url

    @HttpExceptionWrapper
    async def get_booking_from_date(self, db: AsyncSession, stadium_id: int, date: str):
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
        result = self.booking_repository.get_booking_from_date(db=db, stadium_id=stadium_id,
                                                               selected_date=selected_date)
        return result

    @HttpExceptionWrapper
    async def booking_stadium(self, db: AsyncSession, stadium_id: int, user: User):
        return await self.booking_repository.base_filter(db, Booking.stadium_id == stadium_id,
                                                         options=[selectinload(Booking.stadium),
                                                                  selectinload(Booking.user)])

    @HttpExceptionWrapper
    async def get_booking(self, db: AsyncSession, booking_id: int, ):
        return await self.booking_repository.get_or_404(db=db, object_id=booking_id,
                                                        options=[selectinload(Booking.stadium),
                                                                 selectinload(Booking.user)])

    @HttpExceptionWrapper
    async def get_bookings_user(self, db: AsyncSession, user: User):
        return await self.booking_repository.base_filter(db, Booking.user_id == user.id,
                                                         options=[selectinload(Booking.stadium)])

    @HttpExceptionWrapper
    async def bookings_for_vendor(self, db: AsyncSession, user: User, page: int, size: int):
        query = (
            select(Booking)
            .join(Booking.stadium)
            .where(Stadium.user_id == user.id)
            .options(
                selectinload(Booking.stadium),
                selectinload(Booking.user)
            )
        )

        # Получаем данные с пагинацией
        paginated_data = await self.booking_repository.paginate(query, db, page, size)
        return PaginatedBookingsResponse(**paginated_data)

    @HttpExceptionWrapper
    async def delete_booking(self, db: AsyncSession, user: User, booking_id: int):
        booking = await self.booking_repository.get_or_404(db=db, object_id=booking_id)
        if not booking.status == StatusBooking.PENDING:
            raise HTTPException(status_code=400, detail="Удалять бронирования можно только со статусом 'Pending'")

        self.permission.check_owner_or_admin(current_user=user, model=booking)
        await self.booking_repository.cancel_booking(db, existing_booking=booking)
        return {"msg": "Бронирование и связанные услуги успешно удалены"}
