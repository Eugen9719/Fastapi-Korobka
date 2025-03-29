from typing import Any, List

from fastapi import APIRouter

from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.services import facility_service
from backend.app.models.additional_facility import FacilityRead, FacilityCreate
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import SessionDep

services_router = APIRouter()


@services_router.post("/create", response_model=List[FacilityRead])
@sentry_capture_exceptions
async def create_facility(db: SessionDep, schema: List[FacilityCreate], user:CurrentUser) -> Any:
    return await facility_service.create_facility(db, schema=schema, user=user)
