from fastapi import HTTPException, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.interface.utils.i_image_handler import ImageHandler
from backend.app.interface.utils.i_password_service import IPasswordService
from backend.app.models import User
from backend.app.models.auth import Msg
from backend.app.models.users import UpdatePassword, UserUpdate
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.email.email_service import EmailService
from backend.app.services.auth.permission import PermissionService


class UserService:
    """Сервис управления пользователями"""

    def __init__(self, user_repository: IUserRepository, permission: PermissionService, pass_service: IPasswordService,
                 email_service: EmailService, image_handler: ImageHandler):
        self.user_repository = user_repository
        self.permission = permission
        self.pass_service = pass_service
        self.image_handler = image_handler
        self.email_service = email_service

    @HttpExceptionWrapper
    async def update_user(self, db: AsyncSession, schema: UserUpdate, model: User) -> User:
        """Обновление данных пользователя с проверкой уникальности email."""
        existing_user = await self.user_repository.get_by_email(db, email=schema.email)
        if existing_user and existing_user.id != model.id:
            raise HTTPException(status_code=400, detail="Email is already in use by another user.")
        return await self.user_repository.update(db=db, model=model, schema=schema)

    @HttpExceptionWrapper
    async def update_password(self, db: AsyncSession, model: User, schema: UpdatePassword) -> Msg:
        """Обновление пароля"""
        if not self.pass_service.verify_password(schema.current_password, model.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        if schema.current_password == schema.new_password:
            raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")
        model.hashed_password = self.pass_service.hash_password(schema.new_password)
        await self.user_repository.save_db(db, model)
        return Msg(msg="Пароль обновлен успешно")

    @HttpExceptionWrapper
    async def password_recovery(self, db: AsyncSession, email, ):
        user = await self.user_repository.get_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Пользователя с этим email нет в системе')
        password_reset_token = self.pass_service.generate_password_reset_token(email)
        await self.email_service.send_reset_password(email_to=user.email, email=email, token=password_reset_token)
        return {"msg": "Сброс пароля отправлен на email"}

    @HttpExceptionWrapper
    async def password_reset(self, db: AsyncSession, token: str, new_password: str):
        email = self.pass_service.verify_password_reset_token(token)
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невалидный токен")

        user = await self.user_repository.get_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователя с этим email нет в системе")

        self.permission.verify_active(user)
        user.hashed_password = self.pass_service.hash_password(new_password)
        await self.user_repository.save_db(db, user)
        return {"msg": "Пароль успешно изменен"}

    @HttpExceptionWrapper
    async def upload_image(self, db: AsyncSession, current_user: User, file: UploadFile = File(...)) -> dict:
        """Загрузка изображения для пользователя."""
        user = await self.user_repository.get_or_404(db, id=current_user.id)
        self.permission.check_owner_or_admin(current_user=current_user, model=user)
        await self.image_handler.delete_old_image(db, user)
        return await self.image_handler.upload_image(db, user, file)

    @HttpExceptionWrapper
    async def delete_user(self, db: AsyncSession, current_user: User, user_id: int) -> Msg:
        """Удаление пользователя с проверкой прав."""
        target_user = await self.user_repository.get_or_404(db, id=user_id)
        self.permission.check_delete_permission(current_user, target_user)
        await self.user_repository.remove(db=db, id=target_user.id)
        return Msg(msg="Пользователь удален успешно")
