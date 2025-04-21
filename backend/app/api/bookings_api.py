import stripe
from typing import List
from fastapi import APIRouter, Query
from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.service_factory import service_factory
from backend.app.models.auth import Msg
from backend.app.models.bookings import BookingCreate, BookingRead, BookingReadGet, PaginatedBookingsResponse
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.config import settings
from backend.core.db import SessionDep, TransactionSessionDep
from datetime import date

stripe.api_key = settings.STRIPE_SECRET_KEY
booking_router = APIRouter()


@booking_router.post('/create', response_model=BookingRead)
@sentry_capture_exceptions
async def create_booking(schema: BookingCreate, db: TransactionSessionDep, user: CurrentUser):
    """
    Создание новой брони стадиона.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь
    :param schema: Данные для создания бронирования
    :return: Созданное бронирование в формате BookingRead
    """
    return await service_factory.booking_service.create_booking(db=db, schema=schema, user=user)


@booking_router.post('/pay/{booking_id}', response_model=dict)
@sentry_capture_exceptions
async def create_payment_session(booking_id: int, db: SessionDep, user: CurrentUser):
    """
    Создание платежной сессии для бронирования.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь
    :param booking_id: ID бронирования для оплаты
    :return: Ссылка для оплаты в формате {"payment_url": "url"}
    """
    success_url = "http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "http://localhost:8000/cancel"
    payment_url = await service_factory.booking_service.create_payment_session(
        db=db,
        booking_id=booking_id,
        success_url=success_url,
        cancel_url=cancel_url
    )
    return {"payment_url": payment_url}


@booking_router.get("/booking_from_date", response_model=List[BookingRead])
@sentry_capture_exceptions
async def booking_from_date(db: SessionDep, stadium_id: int, selected_date: date):
    """
    Получение списка бронирований стадиона на указанную дату.

    :param db: Сессия базы данных
    :param stadium_id: ID стадиона
    :param selected_date: Дата для проверки бронирований
    :return: Список бронирований на указанную дату
    """
    return await service_factory.booking_service.get_booking_from_date(db=db, stadium_id=stadium_id, date=selected_date)


@booking_router.get("/bookings-vendor", response_model=PaginatedBookingsResponse)
@sentry_capture_exceptions
async def bookings_vendor(db: SessionDep, user: CurrentUser, page: int = Query(1, ge=1), size: int = Query(2, le=100)):
    """
    Получение пагинированного списка бронирований для владельца стадиона.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь (владелец)
    :param page: Номер страницы (начиная с 1)
    :param size: Количество элементов на странице (максимум 100)
    :return: Пагинированный список бронирований
    """
    return await service_factory.booking_service.bookings_for_vendor(db, user, page, size)


@booking_router.get("/booking_vendor/{booking_id}", response_model=BookingReadGet)
@sentry_capture_exceptions
async def get_booking(db: SessionDep, booking_id: int):
    """
    Получение детальной информации о конкретном бронировании.

    :param db: Сессия базы данных
    :param booking_id: ID бронирования
    :return: Подробная информация о бронировании
    """
    return await service_factory.booking_service.get_booking(db=db, booking_id=booking_id)


@booking_router.get('/{stadium_id}/stadium', response_model=List[BookingReadGet])
@sentry_capture_exceptions
async def booking_for_stadium(db: SessionDep, stadium_id: int, user: CurrentUser):
    """
    Получение списка бронирований для конкретного стадиона.

    :param db: Сессия базы данных
    :param stadium_id: ID стадиона
    :param user: Текущий авторизованный пользователь
    :return: Список бронирований стадиона
    """
    return await service_factory.booking_service.booking_stadium(db=db, stadium_id=stadium_id, user=user)


@booking_router.get('/booking_user', response_model=List[BookingReadGet])
@sentry_capture_exceptions
async def booking_for_user(db: SessionDep, user: CurrentUser):
    """
    Получение списка бронирований текущего пользователя.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь
    :return: Список бронирований пользователя
    """
    return await service_factory.booking_service.get_bookings_user(db, user)


@booking_router.delete("/delete/{booking_id}")
@sentry_capture_exceptions
async def delete_booking(db: TransactionSessionDep, current_user: CurrentUser, booking_id: int) -> Msg:
    """
    Удаление бронирования.

    :param db: Сессия базы данных
    :param current_user: Текущий авторизованный пользователь
    :param booking_id: ID бронирования для удаления
    :return: Сообщение о результате операции
    """
    return await service_factory.booking_service.delete_booking(db, booking_id=booking_id, user=current_user)
#
# @booking_router.get('/{booking_id}/services', response_model=List[BookingServiceRead])
# @sentry_capture_exceptions
# async def get_booking_services(booking_id: int, db: SessionDep):
#     return await booking_repo.get_booking_services_by_id(db, booking_id)
#
