from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Query
from backend.app.dependencies.auth_dep import CurrentUser, SuperUser, OwnerUser
from backend.app.dependencies.services import stadium_service
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
    return await stadium_service.create_stadium(db, schema=schema, user=current_user)


@stadium_router.put("/update/{stadium_id}", response_model=StadiumsRead)
@sentry_capture_exceptions
async def update_stadium(db: TransactionSessionDep, current_user: CurrentUser, stadium_id: int, schema: StadiumsUpdate):
    """
    Обновляет информацию о стадионе.

    **Параметры:**
    - `stadium_id` (int): Идентификатор стадиона, который необходимо обновить.
    - `schema` (StadiumsUpdate): Объект с данными для обновления стадиона
    - `current_user` (CurrentUser): Текущий авторизованный пользователь. Обязательный параметр.
    Он будет проверен на права доступа (должен быть администратором или владельцем стадиона).
    """
    return await stadium_service.update_stadium(db, schema=schema, stadium_id=stadium_id, user=current_user)


@stadium_router.delete("/delete/{stadium_id}")
@sentry_capture_exceptions
async def delete_stadium(db: TransactionSessionDep, current_user: CurrentUser, stadium_id: int) -> Msg:
    """
    Удаляет стадион по указанному идентификатору.

    **Параметры:**
    - `stadium_id` (int): Идентификатор стадиона, который нужно удалить.
    - `current_user` (CurrentUser): Текущий пользователь, который выполняет операцию.
    **Ответ:**
    - Возвращает сообщение о результате выполнения операции (успешно или ошибка).
    """
    return await stadium_service.delete_stadium(db, stadium_id=stadium_id, user=current_user)


@stadium_router.patch('/start-verification/{stadium_id}', response_model=StadiumsRead)
@sentry_capture_exceptions
async def start_verification(stadium_id: int, db: TransactionSessionDep, user: CurrentUser):
    """
    Запускает процесс верификации стадиона, обновляя его статус на "Верификация".
    """
    return await stadium_service.verify_stadium(
        db=db, schema=StadiumVerificationUpdate(status=StadiumStatus.VERIFICATION), stadium_id=stadium_id, user=user)


@stadium_router.patch('/approve/{stadium_id}', response_model=StadiumsRead)
@sentry_capture_exceptions
async def approve_verification(stadium_id: int, schema: StadiumVerificationUpdate, db: TransactionSessionDep,
                               user: SuperUser):
    """
    Ожидает одобрения верификации стадиона администратором и обновляет его статус на "Одобрен".

    **Параметры:**
    - `stadium_id` (int): Идентификатор стадиона, который будет одобрен.
    - `schema` (StadiumVerificationUpdate): Обновленные данные для верификации стадиона, включая новый статус
    (например,"Added" - "Одобрен").
    Варианты статуса для админа: "Added", "Rejected", "Needs_revision"
    """
    return await stadium_service.approve_verification_by_admin(db=db, schema=schema, stadium_id=stadium_id, user=user)


@stadium_router.put("/upload/{stadium_id}", response_model=dict)
@sentry_capture_exceptions
async def upload_image_stadium(db: TransactionSessionDep, stadium_id: int, user: CurrentUser,
                               file: UploadFile = File()):
    """
        Загружает изображение для стадиона.

        **Параметры:**
        - `stadium_id` (int): Идентификатор стадиона, для которого загружается изображение.
        - `file` (UploadFile): Изображение, которое нужно загрузить.
    """
    return await stadium_service.upload_image(db=db, stadium_id=stadium_id, user=user, file=file)


@stadium_router.get('/all', response_model=List[StadiumsRead])
@sentry_capture_exceptions
async def get_stadiums(db: SessionDep):
    return await stadium_service.get_stadiums(db=db)


@stadium_router.get('/vendors-stadiums', response_model=PaginatedStadiumsResponse)
@sentry_capture_exceptions
async def get_vendor_stadiums(db: SessionDep, user: OwnerUser, page: int = Query(1, ge=1),
                              size: int = Query(2, le=100)) -> PaginatedStadiumsResponse:
    return await stadium_service.get_vendor_stadiums(db, user, page, size)


@stadium_router.get("/detail/{stadium_id}", response_model=StadiumsReadWithFacility)
@sentry_capture_exceptions
async def detail_stadium(db: SessionDep, stadium_id: int):
    """
        Получает информацию о стадионе и его услугах по идентификатору стадиона.

        **Параметры:**
        - `stadium_id`: Идентификатор стадиона.

        **Ответ:**
        - Стадион с привязанными услугами, отзывами.
        """
    return await stadium_service.detail_stadium(db, stadium_id=stadium_id)


@stadium_router.post("/services/{stadium_id}/")
@sentry_capture_exceptions
async def add_facility_to_stadium(db: TransactionSessionDep, stadium_id: int, schema: List[StadiumFacilityCreate],
                                  user: CurrentUser):
    """
    Добавляет услуги для указанного стадиона.

        - `stadium_id` (int): ID стадиона, для которого добавляются услуги.
        - `schema` (List[StadiumServiceCreate]): Список объектов, с id услуги, которые нужно добавить.
        **Возвращает**:
        - Список объектов `StadiumServiceRead`, где указаны добавленные услуги.
    """
    return await stadium_service.add_facility_stadium(db=db, stadium_id=stadium_id, facility_schema=schema, user=user)


@stadium_router.delete("/delete-service", response_model=dict)
@sentry_capture_exceptions
async def stadium_delete_facility(db: TransactionSessionDep, schema: StadiumFacilityDelete, user: CurrentUser):
    """
    Удаляет услугу у стадиона.

    **Параметры:**
    - `schema` (StadiumServiceDelete): Схема, содержит информацию об id стадиона и id услуге, которую нужно удалить


    **Ответ:**
    - Возвращает результат операции в виде словаря с подтверждением выполнения удаления.

    """
    return await stadium_service.delete_facility_from_stadium(db, schema=schema, user=user)


@stadium_router.get('/search', response_model=List[StadiumsRead])
@sentry_capture_exceptions
async def stadium_search(db: SessionDep, city: str, start_time: datetime, end_time: datetime):
    return await stadium_service.get_available_stadiums(db, city=city, start_time=start_time, end_time=end_time)
