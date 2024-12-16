import logging
import uuid
import pytest
from datetime import timedelta

from fastapi import status, HTTPException
from fastapi.encoders import jsonable_encoder

from sqlmodel import Session

from backend.app.base.auth.auth_service import verify_registration_user
from backend.app.base.auth.permissions import get_current_user, get_superuser, get_owner
from backend.app.models import User
from backend.app.models.auth import VerificationCreate, VerificationOut
from backend.app.models.users import UserUpdate
from backend.app.repositories.auth_repositories import auth_repository
from backend.app.repositories.user_repositories import user_repository
from backend.core import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("db", "create_user", "create_superuser")
class TestPermissions:
    def test_get_current_user(self, db, create_user) -> None:
        user, _ = create_user()
        token = security.create_access_token(user.id, expires_delta=timedelta(600))
        result_user = get_current_user(db, token)
        assert result_user.id == user.id

    def test_get_current_user_invalid_token(self, db: Session) -> None:
        """Тест с недействительным токеном """
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db, invalid_token)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Could not validate credentials"

    def test_get_current_user_not_found(self, db: Session) -> None:
        """Тест на случай, когда пользователь не найден """
        invalid_user_id = 9999
        token = security.create_access_token(invalid_user_id, expires_delta=timedelta(600))

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db, token)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    @pytest.mark.parametrize("user_id, is_vendor, expected_exception", [
        (2, True, None),  # Пользователь с ролью "продавец", исключений быть не должно
        (4, False, HTTPException),  # Пользователь не "продавец", должно быть исключение
    ])
    def test_get_vendor_user(self, db, user_id, is_vendor, expected_exception):
        token = security.create_access_token(user_id, expires_delta=timedelta(600))
        current_user = get_current_user(db, token)
        # Тестирование функции get_vendor
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                get_owner(current_user)
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "This user not owner"
        else:
            result = get_owner(current_user)
            assert result.status == "OWNER"

    @pytest.mark.parametrize("user_id, is_superuser, expected_exception", [
        (3, True, None),
        (4, False, HTTPException),
    ])
    def test_get_superuser(self, db, user_id, is_superuser, expected_exception):
        token = security.create_access_token(user_id, expires_delta=timedelta(600))
        current_user = get_current_user(db, token)
        # Тестирование функции get_vendor
        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                get_superuser(current_user)
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "The user doesn't have enough privileges"
        else:
            result = get_superuser(current_user)
            assert result.is_superuser == True


class TestCrudUser:
    def test_get_user(self, db: Session, create_user) -> None:
        user, password = create_user()
        # Получение пользователя по id
        user_2 = db.get(User, user.id)
        assert user_2
        assert user.email == user_2.email

        assert jsonable_encoder(user) == jsonable_encoder(user_2)

    def test_update_user(self, db: Session, create_user):
        user, _ = create_user()  # Получаем существующего пользователя

        # Создаем данные для обновления
        update_data = UserUpdate(
            email="newemail@example.com",
            first_name="NewFirstName",
            last_name="NewLastName"
        )

        # Обновляем пользователя
        updated_user = user_repository.update(db=db, model=user, schema=update_data)

        # Проверяем, что данные обновлены
        assert updated_user.email == update_data.email
        assert updated_user.first_name == update_data.first_name
        assert updated_user.last_name == update_data.last_name

    def test_is_active(self, db: Session, create_user):
        user, password = create_user()
        # Проверяем статус активности пользователя
        is_active = user_repository.is_active(user)
        # Проверяем, что пользователь не активен по умолчанию
        assert is_active is False

    def test_verify_registration_user_success(self, db: Session, create_user):
        user, password = create_user()
        # Создаем верификацию
        verification = auth_repository.create(db, schema=VerificationCreate(user_id=user.id))

        # Выполняем верификацию
        result = verify_registration_user(VerificationOut(link=verification.link), db)
        assert result is True

        # Проверяем, что пользователь активирован
        updated_user = user_repository.get(db, id=user.id)
        assert updated_user.is_active is True

    def test_verify_registration_user_failure(self, db: Session):
        # Пытаемся верифицировать с несуществующим UUID
        nonexistent_uuid = uuid.uuid4()  # Генерация случайного UUID
        result = verify_registration_user(VerificationOut(link=nonexistent_uuid), db)
        assert result is False

    def test_get_by_email(self, db: Session, create_user):
        user = user_repository.get(db=db, id=1)
        get_user_email = user_repository.get_by_email(db=db, email="vendor@gmail.com")
        assert user == get_user_email

    @pytest.mark.parametrize("email, password, expected_status", [
        ("admin@gmail.com", "mars03051972", True),  # Успешная аутентификация
        ("vendodfdsfr@gmail.com", "mars03051972", None),  # Неверный email
        ("vendor@gmail.com", "mars0305197sdaf2", None),  # Неверный пароль
    ])
    def test_authenticate(self, db: Session, email, password, expected_status):
        authenticated_user = user_repository.authenticate(db, email=email, password=password)
        if expected_status:
            assert authenticated_user is not None
        else:
            assert authenticated_user is None
