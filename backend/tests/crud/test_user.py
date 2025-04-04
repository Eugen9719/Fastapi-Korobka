import logging
import uuid

import pytest
from datetime import timedelta
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth_dep import get_current_user
from backend.app.dependencies.repositories import user_repo
from backend.app.models.auth import VerificationOut, VerificationCreate
from backend.app.models.users import UserUpdate, UpdatePassword, UserCreate, StatusEnum

from backend.core import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.run(order=1)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "create_user", "create_superuser")
class TestPermissions:
    async def test_get_current_user(self, db, create_user) -> None:
        user, _ = await create_user()
        token = security.create_access_token(user.id, expires_delta=timedelta(600))
        result_user = await get_current_user(db, token)
        assert result_user.id == user.id

    async def test_get_current_user_invalid_token(self, db: AsyncSession) -> None:
        """Тест с недействительным токеном """
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db, invalid_token)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Could not validate credentials"

    async def test_get_current_user_not_found(self, db: AsyncSession) -> None:
        """Тест на случай, когда пользователь не найден """
        invalid_user_id = 9999
        token = security.create_access_token(invalid_user_id, expires_delta=timedelta(600))

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db, token)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Объект не найден"

    # @pytest.mark.parametrize("user_id, is_vendor, expected_exception", [
    #     (2, True, None),  # Пользователь с ролью "продавец", исключений быть не должно
    #     (4, False, HTTPException),  # Пользователь не "продавец", должно быть исключение
    # ])
    # async def test_get_vendor_user(self, db, user_id, is_vendor, expected_exception):
    #     token = security.create_access_token(user_id, expires_delta=timedelta(600))
    #     current_user = await get_current_user(db, token)
    #     # Тестирование функции get_vendor
    #     if expected_exception:
    #         with pytest.raises(expected_exception) as exc_info:
    #              await get_owner(current_user)
    #         assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    #         assert exc_info.value.detail == "This user is not an owner"
    #     else:
    #         result = await get_owner(current_user)
    #         assert result.status == "OWNER"

    # @pytest.mark.parametrize("user_id, is_superuser, expected_exception", [
    #     (3, True, None),
    #     (4, False, HTTPException),
    # ])
    # async def test_get_superuser(self, db, user_id, is_superuser, expected_exception):
    #     logger.info(f"Начало теста: {self.test_get_superuser.__name__}")
    #     token = security.create_access_token(user_id, expires_delta=timedelta(600))
    #     current_user = await get_current_user(db, token)
    #     # Тестирование функции get_vendor
    #     if expected_exception:
    #         with pytest.raises(expected_exception) as exc_info:
    #             get_superuser(current_user)
    #         assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    #         assert exc_info.value.detail == "The user doesn't have enough privileges"
    #     else:
    #         result = get_superuser(current_user)
    #         assert result.is_superuser == True


@pytest.mark.run(order=1)
@pytest.mark.anyio
class TestCrudUser:

    @pytest.mark.parametrize("email, password, expected_status", [
        ("admin@gmail.com", "mars03051972", True),  # Успешная аутентификация
        ("vendodfdsfr@gmail.com", "mars03051972", None),  # Неверный email
        ("vendor@gmail.com", "mars0305197sdaf2", None),  # Неверный пароль
    ])
    async def test_authenticate(self, db: AsyncSession, email, password, expected_status):
        authenticated_user = await user_repo.authenticate(db, email=email, password=password)
        # Проверяем результат
        if expected_status:
            assert authenticated_user is not None
            assert authenticated_user.email == email
        else:
            assert authenticated_user is None

    @pytest.mark.parametrize("user_id, update_email,first_name, expected_exception, status_code, detail", [
        (1, "vendor@gmail.com", "NewFirstName", None, None, None),
        (1, "vendor1@gmail.com", "NewFirstName", HTTPException, 400,
         "Email is already in use by another user.")  # email уже занят
    ])
    async def test_update_user(self, db: AsyncSession, user_id, update_email, first_name, expected_exception,
                               status_code, detail):

        user = await  user_repo.get_or_404(db=db, id=user_id)

        update_schema = UserUpdate(email=update_email, first_name=first_name, last_name="NewLastName")

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await user_repo.update_user(db=db, model=user, schema=update_schema)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await user_repo.update_user(db=db, model=user, schema=update_schema)
            updated_user = await user_repo.get_by_email(db=db, email=update_email)

            assert updated_user.email == update_email
            assert updated_user.first_name == update_schema.first_name
            assert updated_user.last_name == update_schema.last_name

    @pytest.mark.parametrize("email, current_password,hashed_password, expected_exception, status_code, detail", [
        ("customer6@gmail.com", "mars03051972", "mars03051972", HTTPException, 400,
         "New password cannot be the same as the current one"),
        ("customer6@gmail.com", "mArs03051972", "Mars03051972", HTTPException, 400, "Incorrect password"),
        ("customer6@gmail.com", "mars03051972", "Mars03051972", None, None, None),
    ])
    async def test_update_password(self, db: AsyncSession, email, current_password, hashed_password, expected_exception,
                                   status_code, detail):
        user = await user_repo.get_by_email(db=db, email=email)
        update_schema = UpdatePassword(current_password=current_password, new_password=hashed_password)

        if not expected_exception:
            await user_repo.update_password(db=db, model=user, schema=update_schema)

        else:
            with pytest.raises(expected_exception) as exc_info:
                await user_repo.update_password(db=db, model=user, schema=update_schema)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail

    @pytest.mark.parametrize("user_id, delete_user_id, expected_exception, status_code, detail", [
        (6, 1, HTTPException, status.HTTP_400_BAD_REQUEST,
         "у тебя нет прав удалять других пользователей"),
        (3, 3, HTTPException, status.HTTP_400_BAD_REQUEST, "Админ не может удалить самого себя"),
        (6, 6, None, None, None),
    ])
    async def test_delete_user(self, db: AsyncSession, user_id, delete_user_id, expected_exception,
                               status_code, detail):
        user = await user_repo.get_or_404(db=db, id=user_id)

        if not expected_exception:
            await user_repo.delete_user(db=db, user=user, user_id=user_id, )
        else:
            with pytest.raises(expected_exception) as exc_info:
                await user_repo.delete_user(db=db, user=user, user_id=delete_user_id, )
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail


@pytest.mark.run(order=1)
@pytest.mark.anyio
class TestAuthService:

    @pytest.mark.parametrize("email, expected_exception, status_code, detail", [
        ("adminghfdh@gmail.com", None, None, None),
        ("admin@gmail.com", HTTPException, 400, "Email уже зарегистрирован"),
    ])
    async def test_registration_user(self, db: AsyncSession, email, expected_exception, status_code, detail):
        new_user = UserCreate(
            email=email,
            first_name="string",
            last_name="string",
            avatar="string",
            password="stringst",
            status=StatusEnum.PLAYER
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await registration_user(db=db, new_user=new_user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            response = await registration_user(db=db, new_user=new_user)
            assert response == {"msg": "Письмо с подтверждением отправлено"}

    @pytest.mark.parametrize("expected_exception, status_code, detail", [
        (None, None, None),
        (HTTPException, 404, "Verification failed"),
    ])
    async def test_verify_registration_user_success(self, db: AsyncSession, expected_exception, status_code, detail):
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                nonexistent_uuid = uuid.uuid4()
                await verify_registration_user(VerificationOut(link=nonexistent_uuid), db)

            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            verification = await auth_repo.create(db, schema=VerificationCreate(user_id=5))

            # Выполняем верификацию
            result = await verify_registration_user(VerificationOut(link=verification.link), db)
            assert result == {'msg': 'Email successfully verified'}
            updated_user = await user_repo.get(db, id=5)
            assert updated_user.is_active is True


