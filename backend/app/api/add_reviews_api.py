from fastapi import APIRouter
from backend.app.base.auth.permissions import CurrentUser
from backend.app.base.utils.deps import SessionDep

from backend.app.models.auth import Msg
from backend.app.models.stadiums import CreateReview, ReviewRead, UpdateReview
from backend.app.repositories.stadiums_repositories import stadium_repo, review_repo

add_review_router = APIRouter()


@add_review_router.post('/add-review/{stadium_id}', response_model=ReviewRead)
def add_review(db: SessionDep, user: CurrentUser, schema: CreateReview, stadium_id: int):
    stadium = stadium_repo.get_or_404(db=db, id=stadium_id)
    # Проверяем, оставил ли пользователь отзыв для этого продукта
    review_repo.check_duplicate_review(db=db, user_id=user.id, stadium_id=stadium_id)
    return review_repo.create(db=db, schema=schema, stadium_id=stadium.id, user_id=user.id)


@add_review_router.put('/update_review/{review_id}', response_model=ReviewRead)
def update_review(schema: UpdateReview, db: SessionDep, user: CurrentUser, review_id: int):
    review = review_repo.get_or_404(db=db, id=review_id)
    review_repo.check_current_user_or_admin(current_user=user, model=review)
    return review_repo.update(db, model=review, schema=schema)


@add_review_router.delete("/delete_review/{review_id}", response_model=Msg)
def delete_review(db: SessionDep, review_id: int, user: CurrentUser) -> Msg:
    review = review_repo.get_or_404(db, id=review_id)
    review_repo.check_current_user_or_admin(current_user=user, model=review)
    review_repo.remove(db, id=review.id)
    return Msg(msg="Review deleted successfully")


