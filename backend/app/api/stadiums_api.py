from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException

from ..base.auth.permissions import OwnerUser, SuperUser, CurrentUser
from ..base.utils.deps import SessionDep
from ..models import Stadiums, AdditionalService
from ..models.additional_service import StadiumServiceAdd
from ..models.auth import Msg
from ..models.stadiums import StadiumsCreate, StadiumsRead, StadiumVerificationUpdate, StadiumStatus, StadiumsUpdate
from ..repositories.stadiums_repositories import stadium_repo


stadium_router = APIRouter()


@stadium_router.get('/search', response_model=List[Stadiums])
def stadium_search(db: SessionDep, city: str, start_time: datetime, end_time: datetime, ):
    return stadium_repo.get_available_stadiums(db, city=city, start_time=start_time, end_time=end_time)


@stadium_router.post('/create', response_model=StadiumsRead)
def create_stadium(schema: StadiumsCreate, db: SessionDep, user: OwnerUser):
    if not stadium_repo.slug_unique(db, schema.slug):
        raise HTTPException(status_code=400, detail="Slug already used")
    return stadium_repo.create(db=db, schema=schema, user_id=user.id)


@stadium_router.post('/add_services/{stadium_id}', response_model=StadiumsRead)
def add_services_to_stadium(stadium_id: int, schema: StadiumServiceAdd, db: SessionDep):
    # Получаем стадион по id
    stadium = stadium_repo.get_or_404(db, id=stadium_id)

    # Привязываем существующие сервисы
    if schema.service_ids:
        existing_services = db.query(AdditionalService).filter(AdditionalService.id.in_(schema.service_ids)).all()
        if len(existing_services) != len(schema.service_ids):
            raise HTTPException(status_code=404, detail="Some of the selected services do not exist")
        for service in existing_services:
            service.stadium_id = stadium.id
        db.commit()

    # Добавляем новые сервисы
    if schema.new_services:
        for new_service in schema.new_services:
            service = AdditionalService(
                name=new_service.name,
                description=new_service.description,
                price=new_service.price,
                stadium_id=stadium.id
            )
            db.add(service)
        db.commit()
    db.commit()

    return stadium

@stadium_router.patch('/verification/{stadium_id}', response_model=StadiumsRead)
def verification_stadium(stadium_id: int, schema: StadiumVerificationUpdate, db: SessionDep, user: SuperUser):
    stadium = stadium_repo.get_or_404(db=db, id=stadium_id)
    return stadium_repo.verification(db=db, schema=schema, model=stadium)


@stadium_router.put("/update/{stadium_id}", response_model=StadiumsRead)
def update_stadium(*, db: SessionDep, current_user: CurrentUser, stadium_id: int, schema: StadiumsUpdate) -> Any:
    stadium = stadium_repo.get_or_404(db=db, id=stadium_id)
    stadium_repo.check_current_user_or_admin(current_user=current_user, model=stadium)
    if not current_user.is_superuser:
        stadium.status = StadiumStatus.VERIFICATION
        stadium.is_active = False
    return stadium_repo.update(db, model=stadium, schema=schema)





@stadium_router.get('/all', response_model=List[StadiumsRead])
def get_stadiums(db: SessionDep):
    return stadium_repo.get_many(db=db)


@stadium_router.delete("/delete/{stadium_id}")
def delete_stadiums(db: SessionDep, current_user: CurrentUser, stadium_id: int) -> Msg:
    stadium = stadium_repo.get_or_404(db=db, id=stadium_id)
    stadium_repo.check_current_user_or_admin(current_user=current_user, model=stadium)
    stadium_repo.remove(db, id=stadium.id)
    return Msg(msg="stadium deleted successfully")


@stadium_router.get("/detail/{stadium_id}", response_model=StadiumsRead)
def detail_stadium(db: SessionDep, stadium_id: int) -> Any:
    stadium = stadium_repo.get_or_404(db=db, id=stadium_id)
    return stadium

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