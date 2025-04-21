from typing import Any, List
from fastapi import APIRouter, UploadFile, File

from backend.app.dependencies.auth_dep import CurrentUser, SuperUser
from backend.app.dependencies.service_factory import service_factory

from backend.app.models.auth import Msg
from backend.app.models.users import UserPublic, UserUpdate, UpdatePassword
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import SessionDep, TransactionSessionDep

user_router = APIRouter()


@user_router.get('/me', response_model=UserPublic)
def user_me(current_user: CurrentUser):
    """
    Получение информации о текущем авторизованном пользователе.

    :param current_user: Текущий авторизованный пользователь
    :return: Публичные данные пользователя
    """
    return current_user


@user_router.patch("/me", response_model=UserPublic)
@sentry_capture_exceptions
async def update_user_me(*, db: TransactionSessionDep, schema: UserUpdate, user: CurrentUser) -> Any:
    """
    Обновление данных текущего пользователя.

    :param db: Сессия базы данных
    :param schema: Данные для обновления
    :param user: Текущий авторизованный пользователь
    :return: Обновленные публичные данные пользователя
    """
    return await service_factory.user_service.update_user(db=db, model=user, schema=schema)


@user_router.patch("/me/password", response_model=Msg)
@sentry_capture_exceptions
async def update_password_me(*, db: TransactionSessionDep, schema: UpdatePassword, user: CurrentUser) -> Any:
    """
    Изменение пароля текущего пользователя.

    :param db: Сессия базы данных
    :param schema: Данные для смены пароля (текущий и новый пароль)
    :param user: Текущий авторизованный пользователь
    :return: Сообщение об успешном изменении пароля
    """
    return await service_factory.user_service.update_password(db=db, schema=schema, model=user)


@user_router.patch("/upload-avatar")
@sentry_capture_exceptions
async def upload_image(db: TransactionSessionDep, user: CurrentUser, file: UploadFile = File(...)):
    """
    Загрузка аватара пользователя.

    :param db: Сессия базы данных
    :param user: Текущий авторизованный пользователь
    :param file: Загружаемый файл изображения
    :return: Результат операции загрузки
    """
    return await service_factory.user_service.upload_image(db, file=file, current_user=user)


@user_router.get("/all_user", response_model=List[UserPublic])
@sentry_capture_exceptions
async def get_all_user(db: SessionDep, user: SuperUser):
    """
    Получение списка всех пользователей (только для администратора).

    :param db: Сессия базы данных
    :param user: Авторизованный администратор
    :return: Список публичных данных всех пользователей
    """
    return await service_factory.user_repo.get_many(db=db)


@user_router.delete("/delete/{user_id}", response_model=Msg)
@sentry_capture_exceptions
async def delete_user(user_id: int, db: TransactionSessionDep, user: CurrentUser) -> Msg:
    """
    Удаление пользователя по ID (только для администратора).

    :param db: Сессия базы данных
    :param user_id: ID пользователя для удаления
    :param user: Текущий авторизованный пользователь (администратор)
    :return: Сообщение о результате операции
    """
    return await service_factory.user_service.delete_user(db=db, current_user=user, user_id=user_id)


@user_router.get("/{user_id}", response_model=UserPublic)
@sentry_capture_exceptions
async def read_user_by_id(user_id: int, db: SessionDep, user: SuperUser) -> Any:
    """
    Получение информации о пользователе по ID (только для администратора).

    :param db: Сессия базы данных
    :param user_id: ID запрашиваемого пользователя
    :param user: Авторизованный администратор
    :return: Публичные данные пользователя
    :raises HTTPException: 404 если пользователь не найден
    """
    return await service_factory.user_repo.get_or_404(db, id=user_id)