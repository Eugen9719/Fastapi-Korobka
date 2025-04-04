from fastapi import APIRouter
from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.services import review_service
from backend.app.models.auth import Msg
from backend.app.models.stadiums import CreateReview, ReviewRead, UpdateReview
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import TransactionSessionDep

add_review_router = APIRouter()


@add_review_router.post('/add-review/{stadium_id}', response_model=ReviewRead)
@sentry_capture_exceptions
async def add_review(db: TransactionSessionDep, user: CurrentUser, schema: CreateReview, stadium_id: int):
    """
    Добавление нового отзыва к стадиону.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь
    :param schema: Данные для создания отзыва
    :param stadium_id: ID стадиона для отзыва
    :return: Созданный отзыв в формате ReviewRead
    """
    return await review_service.create_review(db=db, schema=schema, stadium_id=stadium_id, user=user)


@add_review_router.put('/update_review/{review_id}', response_model=ReviewRead)
@sentry_capture_exceptions
async def update_review(schema: UpdateReview, db: TransactionSessionDep, user: CurrentUser, review_id: int):
    """
    Обновление существующего отзыва.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь (автор отзыва)
    :param schema: Новые данные для обновления отзыва
    :param review_id: ID отзыва для обновления
    :return: Обновленный отзыв в формате ReviewRead
    """
    return await review_service.update_review(db, schema=schema, user=user, review_id=review_id)


@add_review_router.delete("/delete_review/{review_id}", response_model=Msg)
@sentry_capture_exceptions
async def delete_review(db: TransactionSessionDep, review_id: int, user: CurrentUser) -> Msg:
    """
    Удаление отзыва по ID.

    :param db: Сессия базы данных
    :param review_id: ID отзыва для удаления
    :param user: Текущий авторизованный пользователь (автор отзыва или администратор)
    :return: Сообщение о результате операции
    """
    return await review_service.delete_review(db, user=user, review_id=review_id)
