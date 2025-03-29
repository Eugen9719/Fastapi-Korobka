
from fastapi import HTTPException
from starlette import status

from backend.app.models import User
from backend.app.models.users import StatusEnum


class PermissionService:
    @staticmethod
    def check_delete_permission(current_user: User, target_user: User):
        """Проверка прав на удаление пользователя."""
        if current_user.is_superuser and current_user.id == target_user.id:
            raise HTTPException(status_code=400, detail="Админ не может удалить самого себя")
        if current_user.id != target_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=400, detail="У тебя нет прав удалять других пользователей")

    @staticmethod
    def check_owner_or_admin(current_user, model: User) -> bool:
            """
            Проверяет, является ли пользователь администратором или создателем объекта.
            """
            if not current_user.is_superuser and model.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Только админ или создатель могут проводить операции")

            # logger.info(f"Проверка пользователь id={current_user.id} на владельца или администратора успешна")
            return True

    @staticmethod
    def check_current_user_or_admin(current_user, model: User) -> bool:
            """
            Проверяет, является ли пользователь администратором или создателем объекта.
            """
            if not current_user.is_superuser and model.id != current_user.id:
                raise HTTPException(status_code=403, detail="Только админ или создатель могут проводить операции")

            # logger.info(f"Проверка пользователь id={current_user.id} на владельца или администратора успешна")
            return True


    @staticmethod
    def verify_active(model: User) -> None:
        """Проверяет, активен ли пользователь"""
        if not model.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт неактивен"
            )

    @staticmethod
    def verify_superuser(model: User) -> None:
        """Проверяет права суперпользователя"""
        if not model.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )

    @staticmethod
    def verify_owner(model: User) -> None:
        """Проверяет права владельца"""
        if model.status != StatusEnum.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права владельца"
            )


