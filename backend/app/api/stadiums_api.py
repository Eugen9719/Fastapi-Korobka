from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Query
from backend.app.dependencies.auth_dep import CurrentUser, SuperUser, OwnerUser
from backend.app.dependencies.service_factory import service_factory
from backend.app.models.additional_facility import StadiumFacilityDelete
from backend.app.models.auth import Msg
from backend.app.models.stadiums import StadiumsRead, PaginatedStadiumsResponse, StadiumsCreate, \
    StadiumsUpdate, StadiumVerificationUpdate, StadiumStatus, StadiumFacilityCreate, StadiumsReadWithFacility
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import SessionDep, TransactionSessionDep

stadium_router = APIRouter()


@stadium_router.post("/create", response_model=StadiumsRead)
@sentry_capture_exceptions
async def create_stadium(db: TransactionSessionDep, current_user: CurrentUser, schema: StadiumsCreate):
    """
    Создание нового стадиона.

    :param db: Сессия базы данных
    :param current_user: Данные текущего пользователя (автоматически извлекаются из токена)
    :param schema: Валидированные данные для создания стадиона
    :return: Созданный стадион в формате StadiumsRead
    """
    return await service_factory.stadium_service.create_stadium(db, schema=schema, user=current_user)


@stadium_router.put("/update/{stadium_id}", response_model=StadiumsRead)
@sentry_capture_exceptions
async def update_stadium(db: TransactionSessionDep, current_user: CurrentUser, stadium_id: int, schema: StadiumsUpdate):
    """
    Обновление информации о стадионе.

    :param db: Сессия базы данных
    :param current_user: Данные текущего пользователя (должен быть администратором или владельцем)
    :param stadium_id: Идентификатор стадиона для обновления
    :param schema: Объект с данными для обновления
    :return: Обновленный стадион в формате StadiumsRead
    """
    return await service_factory.stadium_service.update_stadium(db, schema=schema, stadium_id=stadium_id, user=current_user)


@stadium_router.delete("/delete/{stadium_id}")
@sentry_capture_exceptions
async def delete_stadium(db: TransactionSessionDep, current_user: CurrentUser, stadium_id: int) -> Msg:
    """
    Удаление стадиона по идентификатору.

    :param db: Сессия базы данных
    :param current_user: Данные текущего пользователя (должен быть администратором или владельцем)
    :param stadium_id: Идентификатор стадиона для удаления
    :return: Сообщение о результате операции
    """
    return await service_factory.stadium_service.delete_stadium(db, stadium_id=stadium_id, user=current_user)


@stadium_router.patch('/start-verification/{stadium_id}', response_model=StadiumsRead)
@sentry_capture_exceptions
async def start_verification(stadium_id: int, db: TransactionSessionDep, user: CurrentUser):
    """
    Запуск процесса верификации стадиона.

    :param db: Сессия базы данных
    :param user: Данные текущего пользователя
    :param stadium_id: Идентификатор стадиона для верификации
    :return: Стадион с обновленным статусом "Верификация"
    """
    return await service_factory.stadium_service.verify_stadium(
        db=db, schema=StadiumVerificationUpdate(status=StadiumStatus.VERIFICATION), stadium_id=stadium_id, user=user)


@stadium_router.patch('/approve/{stadium_id}', response_model=StadiumsRead)
@sentry_capture_exceptions
async def approve_verification(stadium_id: int, schema: StadiumVerificationUpdate, db: TransactionSessionDep,
                               user: SuperUser):
    """
    Одобрение верификации стадиона администратором.

    :param db: Сессия базы данных
    :param user: Данные администратора
    :param stadium_id: Идентификатор стадиона для одобрения
    :param schema: Данные для верификации (статус: "Added", "Rejected" или "Needs_revision")
    :return: Стадион с обновленным статусом
    """
    return await service_factory.stadium_service.approve_verification_by_admin(db=db, schema=schema, stadium_id=stadium_id, user=user)


@stadium_router.put("/upload/{stadium_id}", response_model=dict)
@sentry_capture_exceptions
async def upload_image_stadium(db: TransactionSessionDep, stadium_id: int, user: CurrentUser,
                               file: UploadFile = File()):
    """
    Загрузка изображения для стадиона.

    :param db: Сессия базы данных
    :param user: Данные текущего пользователя
    :param stadium_id: Идентификатор стадиона
    :param file: Загружаемое изображение
    :return: Результат операции в виде словаря
    """
    return await service_factory.stadium_service.upload_image(db=db, stadium_id=stadium_id, user=user, file=file)


@stadium_router.get('/all', response_model=List[StadiumsRead])
@sentry_capture_exceptions
async def get_stadiums(db: SessionDep):
    """
    Получение списка всех стадионов.

    :param db: Сессия базы данных
    :return: Список всех стадионов
    """
    return await service_factory.stadium_service.get_stadiums(db=db)


@stadium_router.get('/vendors-stadiums', response_model=PaginatedStadiumsResponse)
@sentry_capture_exceptions
async def get_vendor_stadiums(db: SessionDep, user: OwnerUser, page: int = Query(1, ge=1),
                              size: int = Query(2, le=100)) -> PaginatedStadiumsResponse:
    """
    Получение пагинированного списка стадионов, принадлежащих текущему владельцу (вендору).

    :param db: Зависимость для работы с базой данных (сессия SQLAlchemy)
    :param user: Авторизованный владелец стадионов (извлекается из токена)
    :param page: Номер страницы (начиная с 1), по умолчанию 1
    :param size: Количество элементов на странице (максимум 100), по умолчанию 2
    :return: Объект PaginatedStadiumsResponse с пагинированным списком стадионов:
             - items: List[Stadium] - список стадионов
             - total: int - общее количество стадионов
             - page: int - текущая страница
             - size: int - количество элементов на странице
             - pages: int - общее количество страниц
    """
    return await service_factory.stadium_service.get_vendor_stadiums(db, user, page, size)


@stadium_router.get("/detail/{stadium_id}", response_model=StadiumsReadWithFacility)
@sentry_capture_exceptions
async def detail_stadium(db: SessionDep, stadium_id: int):
    """
    Получение подробной информации о стадионе.

    :param db: Сессия базы данных
    :param stadium_id: Идентификатор стадиона
    :return: Стадион с привязанными услугами и отзывами
    """
    return await service_factory.stadium_service.detail_stadium(db, stadium_id=stadium_id)


@stadium_router.post("/services/{stadium_id}/")
@sentry_capture_exceptions
async def add_facility_to_stadium(db: TransactionSessionDep, stadium_id: int, schema: List[StadiumFacilityCreate],
                                  user: CurrentUser):
    """
    Добавление услуг для стадиона.

    :param db: Сессия базы данных
    :param user: Данные текущего пользователя
    :param stadium_id: Идентификатор стадиона
    :param schema: Список услуг для добавления
    :return: Список добавленных услуг
    """
    return await service_factory.stadium_service.add_facility_stadium(db=db, stadium_id=stadium_id, facility_schema=schema, user=user)


@stadium_router.delete("/delete-service", response_model=dict)
@sentry_capture_exceptions
async def stadium_delete_facility(db: TransactionSessionDep, schema: StadiumFacilityDelete, user: CurrentUser):
    """
    Удаление услуги у стадиона.

    :param db: Сессия базы данных
    :param user: Данные текущего пользователя
    :param schema: Данные для удаления (идентификаторы стадиона и услуги)
    :return: Результат операции в виде словаря
    """
    return await service_factory.stadium_service.delete_facility_from_stadium(db, schema=schema, user=user)


@stadium_router.get('/search', response_model=List[StadiumsRead])
@sentry_capture_exceptions
async def stadium_search(db: SessionDep, city: str, start_time: datetime, end_time: datetime):
    """
    Поиск доступных стадионов по городу и временному интервалу.

    :param db: Сессия базы данных
    :param city: Город для поиска
    :param start_time: Начало временного интервала
    :param end_time: Конец временного интервала
    :return: Список доступных стадионов
    """
    return await service_factory.stadium_service.get_available_stadiums(db, city=city, start_time=start_time, end_time=end_time)
