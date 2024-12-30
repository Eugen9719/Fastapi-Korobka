from fastapi import HTTPException

from sqlmodel import select
from starlette import status

from backend.app.models.auth import Msg
from backend.app.models.users import User, UserCreateAdmin, UserUpdateAdmin, UserCreate, UserUpdate, StatusEnum, \
    UpdatePassword
from backend.app.repositories.base_repositories import AsyncBaseRepository
from backend.core.security import verify_password, get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepositoryAdmin(AsyncBaseRepository[User, UserCreateAdmin, UserUpdateAdmin]):
    def create_user(self, db: AsyncSession, schema: UserCreateAdmin, **kwargs):
        hashed_password = get_password_hash(schema.password)
        return super().create(db, schema, hashed_password=hashed_password, **kwargs)


class UserRepository(AsyncBaseRepository[User, UserCreate, UserUpdate]):
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> User | None:
        db_user = await self.get_by_email(db=db, email=email)
        if not db_user:
            return None
        if not verify_password(password, db_user.hashed_password):
            return None
        return db_user

    async def create(self, db: AsyncSession, *args, schema: UserCreate, **kwargs):
        hashed_password = get_password_hash(schema.password)
        return await super().create(db, schema, hashed_password=hashed_password, **kwargs)

    async def update_user(self, db: AsyncSession, schema: UserUpdate, model: User, ):
        """Обновления текущего пользователя"""
        existing_user = await user_repo.get_by_email(db=db, email=schema.email)
        if existing_user and existing_user.id != model.id:
            raise HTTPException(status_code=400, detail="Email is already in use by another user.")
        return await super().update(db=db, model=model, schema=schema)

    async def update_password(self, db: AsyncSession, model: User, schema: UpdatePassword, ):
        if not verify_password(schema.current_password, model.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        if schema.current_password == schema.new_password:
            raise HTTPException(
                status_code=400, detail="New password cannot be the same as the current one"
            )
        hashed_password = get_password_hash(schema.new_password)
        model.hashed_password = hashed_password
        await self.save_db(db, model)
        return Msg(msg="Password updated successfully")

    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def delete_user(self, db: AsyncSession, user: User, user_id: int):
        current = await user_repo.get_or_404(db, id=user_id)
        if user.is_superuser and user.id == current.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Админ не может удалить самого себя"
            )

        if user.id != current.id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="у тебя нет прав удалять других пользователей"
            )

        await super().remove(db=db, id=user.id)
        return Msg(msg="User deleted successfully")

    @staticmethod
    def is_active(model: User) -> bool:
        return model.is_active

    @staticmethod
    def is_superuser(model: User) -> bool:
        return model.is_superuser

    @staticmethod
    def is_owner(model: User) -> bool:
        if model.status == StatusEnum.OWNER:
            return True
        return False


user_repo = UserRepository(User)
admin_user_repo = UserRepositoryAdmin(User)
