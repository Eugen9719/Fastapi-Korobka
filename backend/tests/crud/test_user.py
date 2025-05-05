import logging
import uuid

import pytest
from datetime import timedelta
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth_dep import get_current_user
from backend.app.dependencies.service_factory import service_factory
from backend.app.models.auth import VerificationOut, VerificationCreate
from backend.app.models.users import UserUpdate, UpdatePassword, UserCreate, StatusEnum

from backend.core import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@pytest.mark.anyio
@pytest.mark.usefixtures("db","test_data")
class TestPermissions:
    async def test_get_current_user(self, db,) -> None:
        user = await service_factory.user_repo.get_by_email(db, "vendor@gmail.com")
        token = security.create_access_token(user.id)
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
        token = security.create_access_token(invalid_user_id)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db, token)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Объект не найден"

    @pytest.mark.parametrize("user_id, expected_exception", [
        (2,None),  # Пользователь с ролью "продавец", исключений быть не должно
        (4, HTTPException),  # Пользователь не "продавец", должно быть исключение
    ])
    async def test_get_vendor_user(self, db, user_id,  expected_exception):

        current_user = await service_factory.user_repo.get_or_404(db, object_id=user_id)
        # Тестирование функции get_vendor
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                  service_factory.permission_service.verify_owner(current_user)
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Требуются права владельца"
        else:
            result =  service_factory.permission_service.verify_owner(current_user)
            assert result == True





@pytest.mark.anyio
@pytest.mark.usefixtures("db","test_data")
class TestCrudUser:

    @pytest.mark.parametrize("email, password, expected_status", [
        ("admin@gmail.com", "mars03051972", True),  # Успешная аутентификация
        ("vendodfdsfr@gmail.com", "mars03051972", None),  # Неверный email
        ("vendor@gmail.com", "mars0305197sdaf2", None),  # Неверный пароль
    ])
    async def test_authenticate(self, db: AsyncSession, email, password, expected_status):
        authenticated_user = await service_factory.user_auth.authenticate(db, email=email, password=password)
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

        user = await  service_factory.user_repo.get_or_404(db=db, object_id=user_id)

        update_schema = UserUpdate(email=update_email, first_name=first_name, last_name="NewLastName")

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await service_factory.user_service.update_user(db=db, model=user, schema=update_schema)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:
            await service_factory.user_service.update_user(db=db, model=user, schema=update_schema)
            updated_user = await service_factory.user_repo.get_by_email(db=db, email=update_email)

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
        user = await service_factory.user_repo.get_by_email(db=db, email=email)
        update_schema = UpdatePassword(current_password=current_password, new_password=hashed_password)

        if not expected_exception:
            await service_factory.user_service.update_password(db=db, model=user, schema=update_schema)

        else:
            with pytest.raises(expected_exception) as exc_info:
                await service_factory.user_service.update_password(db=db, model=user, schema=update_schema)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail

    # @pytest.mark.parametrize("email,expected_exception, status_code, detail", [
    #     ("customer6nmhmg@gmail.com", HTTPException, 404, "Пользователя с этим email нет в системе"),
    #     ("customer6@gmail.com", None, None, None),
    # ])
    # async def test_password_recovery(self, db: AsyncSession, email, expected_exception,
    #                                status_code, detail):
    #     if not expected_exception:
    #         response = await service_factory.user_service.password_recovery(db=db, email=email)
    #         assert response == {"msg": "Сброс пароля отправлен на email"}
    #
    #     else:
    #         with pytest.raises(expected_exception) as exc_info:
    #             await service_factory.user_service.password_recovery(db=db, email=email)
    #         assert exc_info.value.status_code == status_code
    #         assert exc_info.value.detail == detail

    # @pytest.mark.parametrize("email,new_password,expected_exception, status_code, detail", [
    #     ("", 'password', HTTPException, 400, "Невалидный токен"),
    #     ("vendor1hgf@gmail.com", 'password', HTTPException, 404, "Пользователя с этим email нет в системе"),
    #     ("vendor1@gmail.com",'password', None, None, None),
    # ])
    # async def test_password_reset(self, db: AsyncSession, email,new_password, expected_exception,
    #                                  status_code, detail):
    #     token = service_factory.password_service.generate_password_reset_token(email)
    #     if not expected_exception:
    #         response = await service_factory.user_service.password_reset(db=db, token=token, new_password=new_password)
    #         assert response == {"msg": "Пароль успешно изменен"}
    #
    #     else:
    #         with pytest.raises(expected_exception) as exc_info:
    #             await service_factory.user_service.password_reset(db=db, token=token, new_password=new_password)
    #         assert exc_info.value.status_code == status_code
    #         assert exc_info.value.detail == detail

    """
    if not email: 

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невалидный токен") 
        user = await self.user_repository.get_by_email(db, email=email) 
        if not user: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 

                                detail="Пользователя с этим email нет в системе") """





    @pytest.mark.parametrize("user_id, delete_user_id, expected_exception, status_code, detail", [
            (2, 1, HTTPException, 400,"У тебя нет прав удалять других пользователей"),
            (3, 3, HTTPException, 400, "Админ не может удалить самого себя"),
            (1, 1, None, None, None),
        ])
    async def test_delete_user(self, db: AsyncSession, user_id, delete_user_id, expected_exception,
                                   status_code, detail):
            user = await service_factory.user_repo.get_or_404(db=db, object_id=user_id)

            if not expected_exception:
                await service_factory.user_service.delete_user(db=db, current_user=user, user_id=delete_user_id, )
            else:
                with pytest.raises(expected_exception) as exc_info:
                    await service_factory.user_service.delete_user(db=db, current_user=user, user_id=delete_user_id, )
                assert exc_info.value.status_code == status_code
                assert exc_info.value.detail == detail




@pytest.mark.anyio
@pytest.mark.usefixtures("db","test_data")
class TestAuthService:

    # @pytest.mark.parametrize("email, expected_exception, status_code, detail", [
    #     ("adminghfdh@gmail.com", None, None, None),
    #     ("adminghfdh@gmail.com", HTTPException, 400, "Email уже зарегистрирован"),
    # ])
    # async def test_registration_user(self, db: AsyncSession, email, expected_exception, status_code, detail):
    #     new_user = UserCreate(
    #         email=email,
    #         first_name="string",
    #         last_name="string",
    #         avatar="string",
    #         password="stringst",
    #         status=StatusEnum.PLAYER
    #     )
    #
    #     if expected_exception:
    #         with pytest.raises(expected_exception) as exc_info:
    #             await service_factory.registration_service.register_user(db=db, schema=new_user)
    #         assert exc_info.value.status_code == status_code
    #         assert exc_info.value.detail == detail
    #     else:
    #         response = await service_factory.registration_service.register_user(db=db, schema=new_user)
    #         assert response == {"msg": "Письмо с подтверждением отправлено"}

    @pytest.mark.parametrize("expected_exception, status_code, detail", [
        (None, None, None),
        (HTTPException, 404, "Verification failed"),
    ])
    async def test_verify_registration_user_success(self, db: AsyncSession, expected_exception, status_code, detail):
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                nonexistent_uuid = uuid.uuid4()
                await service_factory.registration_service.verify_user(VerificationOut(link=str(nonexistent_uuid)) , db)

            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail
        else:

            verification = await service_factory.verify_repo.create(db, schema=VerificationCreate(user_id=5))

            # Выполняем верификацию
            result = await service_factory.registration_service.verify_user(VerificationOut(link=verification.link), db)
            assert result == {'msg': "Email успешно подтвержден"}
            updated_user = await service_factory.user_repo.get(db, id=5)
            assert updated_user.is_active is True


