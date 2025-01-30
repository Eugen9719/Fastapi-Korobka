from datetime import datetime
from typing import Any, List

from fastapi import APIRouter

from backend.app.services.auth.permissions import OwnerUser, SuperUser, CurrentUser

from ..models import Stadiums
from ..models.additional_service import StadiumServiceAdd
from ..models.auth import Msg
from ..models.stadiums import StadiumsCreate, StadiumsRead, StadiumVerificationUpdate, StadiumsUpdate
from ..repositories.stadiums_repositories import stadium_repo
from ...core.db import SessionDep

stadium_router = APIRouter()


@stadium_router.get('/search', response_model=List[Stadiums])
async def stadium_search(db: SessionDep, city: str, start_time: datetime, end_time: datetime, ):
    return await stadium_repo.get_available_stadiums(db, city=city, start_time=start_time, end_time=end_time)


@stadium_router.post('/create', response_model=StadiumsRead)
async def create_stadium(stadium_create_data: StadiumsCreate, db: SessionDep, user: OwnerUser):
    return await stadium_repo.create_stadium(db=db, schema=stadium_create_data, user_id=user.id)


@stadium_router.post('/add_services/{stadium_id}', response_model=StadiumsRead)
async def add_services_to_stadium(stadium_id: int, schema: StadiumServiceAdd, db: SessionDep):
    return await stadium_repo.add_services_stadium(db=db, schema=schema, stadium_id=stadium_id)


@stadium_router.patch('/verification/{stadium_id}', response_model=StadiumsRead)
async def verification_stadium(stadium_id: int, schema: StadiumVerificationUpdate, db: SessionDep, user: SuperUser):
    return await stadium_repo.verification(db=db, schema=schema, stadium_id=stadium_id)


@stadium_router.put("/update/{stadium_id}", response_model=StadiumsRead)
async def update_stadium(*, db: SessionDep, current_user: CurrentUser, stadium_id: int, schema: StadiumsUpdate) -> Any:
    return await stadium_repo.update_stadium(db, schema=schema, stadium_id=stadium_id, user=current_user)


@stadium_router.get('/all', response_model=List[StadiumsRead])
async def get_stadiums(db: SessionDep):
    return await stadium_repo.get_many(db=db)



@stadium_router.delete("/delete/{stadium_id}")
async def delete_stadiums(db: SessionDep, current_user: CurrentUser, stadium_id: int) -> Msg:
    return await stadium_repo.delete_stadium(db, stadium_id=stadium_id, user=current_user)


@stadium_router.get("/detail/{stadium_id}", response_model=StadiumsRead)
async def detail_stadium(db: SessionDep, stadium_id: int) -> Any:
    return await stadium_repo.get_or_404(db=db, id=stadium_id)

@stadium_router.get('/detail_slug/{stadium_slug}', response_model=StadiumsRead)
async def get_stadium(db: SessionDep, stadium_slug:str):
    return await stadium_repo.get(db=db, slug=stadium_slug)

# @stadium_router.post("/add_stadium-image", response_model=StadiumsRead)
# def add_stadium_image(
#         db: SessionDep,
#         stadium_id: Optional[int] = Form(None),
#         image: UploadFile = File(None)
# ):
#     # Проверка на наличие category_id
#     if not stadium_id:
#         raise HTTPException(status_code=400, detail="Product ID is required")
#     return stadium_repo.add_image_product(db=db, stadium_id=stadium_id, image=image)
