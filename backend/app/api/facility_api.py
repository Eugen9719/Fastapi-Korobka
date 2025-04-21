from typing import Any, List

from fastapi import APIRouter

from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.service_factory import service_factory
from backend.app.models.additional_facility import FacilityRead, FacilityCreate
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import  TransactionSessionDep

services_router = APIRouter()


@services_router.post("/create", response_model=List[FacilityRead])
@sentry_capture_exceptions
async def create_facility(db: TransactionSessionDep, schema: List[FacilityCreate], user: CurrentUser) -> Any:
    """
    Создание новых услуг/удобств для стадионов.

    :param db: Сессия базы данных
    :param schema: Список данных для создания услуг (название, описание и т.д.)
    :param user: Текущий авторизованный пользователь
    :return: Список созданных услуг в формате FacilityRead
    """
    return await service_factory.facility_service.create_facility(db, schema=schema, user=user)
