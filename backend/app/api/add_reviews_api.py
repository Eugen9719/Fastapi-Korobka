from fastapi import APIRouter
from backend.app.base.auth.permissions import CurrentUser
from backend.app.base.utils.deps import SessionDep

from backend.app.models.auth import Msg
from backend.app.models.stadiums import CreateReview, ReviewRead, UpdateReview
from backend.app.repositories.stadiums_repositories import stadium_repo, review_repo

add_review_router = APIRouter()


@add_review_router.post('/add-review/{stadium_id}', response_model=ReviewRead)
async def add_review(db: SessionDep, user: CurrentUser, schema: CreateReview, stadium_id: int):
    return await review_repo.create_review(db=db, schema=schema, stadium_id=stadium_id, user=user)


@add_review_router.put('/update_review/{review_id}', response_model=ReviewRead)
async def update_review(schema: UpdateReview, db: SessionDep, user: CurrentUser, review_id: int):
    return await review_repo.update_review(db, schema=schema, user=user, review_id=review_id)


@add_review_router.delete("/delete_review/{review_id}", response_model=Msg)
async def delete_review(db: SessionDep, review_id: int, user: CurrentUser) -> Msg:
    return await review_repo.delete_review(db, user=user, review_id=review_id)
