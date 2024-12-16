import logging
import uuid
import pytest
from unittest.mock import patch, ANY

from fastapi.testclient import TestClient
from fastapi import status
from sqlmodel import Session

from backend.app.base.auth.auth_service import generate_password_reset_token, verify_password_reset_token
from backend.app.models.auth import VerificationCreate
from backend.app.repositories.auth_repositories import auth_repository
from backend.tests.utils.utils import random_lower_string, random_email

from backend.core.config import settings

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

password_recovery_data = [
    ("customer@gmail.com", 200, None),  # Существующий пользователь
    ("nonexistent@example.com", status.HTTP_404_NOT_FOUND,{"detail": "The user with this username does not exist in the system"}),
]


@pytest.mark.api
@pytest.mark.usefixtures("db", "client", "create_user")
class TestAuthUser:
    @patch("backend.app.base.auth.auth_service.send_new_account_email")
    def test_registration_new_user(self, mock_send_email, client: TestClient, db: Session):
        logger.info("Начало теста регистрации нового пользователя")

        # Генерация случайных данных для нового пользователя
        email = random_email()
        password = random_lower_string()

        logger.debug(f"Сгенерированные данные пользователя: email={email}, ")

        login_data = {
            "email": email,
            "password": password,
        }

        # Регистрируем нового пользователя
        logger.info("Отправляем запрос на регистрацию пользователя")
        response = client.post(f"{settings.API_V1_STR}/auth/registration", json=login_data)
        assert response.status_code == 200
        logger.info("Пользователь успешно зарегистрирован")

        # Пытаемся зарегистрировать пользователя снова и ожидаем исключение
        logger.info("Отправляем повторный запрос на регистрацию с теми же данными")
        response = client.post(f"{settings.API_V1_STR}/auth/registration", json=login_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"
        logger.info("Попытка повторной регистрации завершилась с ожидаемой ошибкой: Email already registered")

        # Проверяем, что функция отправки письма была вызвана
        logger.info("Проверяем вызов функции отправки письма")
        mock_send_email.assert_called_once_with(
            ANY, ANY, ANY, ANY
        )
        logger.info("Функция отправки письма вызвана один раз с корректными параметрами")

    @pytest.mark.parametrize(
        "email, password, status_code, detail",
        [
            ("vendor@gmail.com", "mars03051972", 200, None),
            ("vendor@gmail.com", "mars0305197288", status.HTTP_400_BAD_REQUEST,{"detail": "Incorrect email or password"}),
            ("customer1@gmail.com", "mars03051972", status.HTTP_400_BAD_REQUEST, {"detail": "Inactive user"}),
        ]
    )
    def test_login_access_token(self, db, client: TestClient, prepare_data, email, password, status_code, detail):
        """Тест на получение access token с различными комбинациями email и пароля."""
        login_data = {
            "username": email,
            "password": password,
        }

        # Отправляем POST запрос на получение access-token
        response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

        # Проверка ответа
        assert response.status_code == status_code
        if response.status_code == 200:
            tokens = response.json()
            assert "access_token" in tokens
            assert tokens["access_token"]
            assert tokens["token_type"] == "bearer"
        else:
            assert response.json() == detail

    def test_confirm_email_success(self, db: Session, client: TestClient, create_user) -> None:
        """Тест успешного подтверждения email"""
        user, _ = create_user()

        # Создаем верификационный объект для подтверждения
        verification = auth_repository.create(db, schema=VerificationCreate(user_id=user.id))

        # Отправляем POST запрос на подтверждение email
        response = client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": str(verification.link)})

        # Проверяем, что статус ответа 200 и содержится соответствующее сообщение
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"msg": "Success verify email"}

    def test_confirm_email_failure(self, db: Session, client: TestClient) -> None:
        """Тест неудачного подтверждения email"""
        # Отправляем POST запрос с неверным UUID
        invalid_uuid = str(uuid.uuid4())
        response = client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": invalid_uuid})

        # Проверяем, что статус ответа 404 и содержится соответствующее сообщение об ошибке
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Verification failed"}

    @pytest.mark.parametrize("email, status_code, detail", password_recovery_data)
    def test_password_recovery(self, db: Session, client: TestClient, email, status_code, detail):
        response = client.post(f"{settings.API_V1_STR}/auth/password-recovery/{email}", )
        # Проверка ответа
        assert response.status_code == status_code
        if status_code == 200:
            # Если статус 200, проверяем сообщение
            assert response.json() == {"msg": "Password recovery email sent"}
        else:
            # Если статус 404, проверяем ошибку
            assert response.json() == detail

    @pytest.mark.parametrize(
        "email, password, status_code, detail",
        [
            ("customer@gmail.com", "Mars03051972", 200, "Password updated successfully"),
        ]
    )
    def test_reset_password(self, db: Session, client: TestClient, email, password, status_code, detail):
        # Создаем токен для теста
        password_reset_token = generate_password_reset_token(email)

        # Эмуляция запроса на изменение пароля
        response = client.post(
            f"{settings.API_V1_STR}/auth/reset_password",
            json={"token": password_reset_token, "new_password": password}
        )

        # Проверка статуса ответа
        assert response.status_code == status_code

        # Проверка содержимого ответа
        response_data = response.json()
        assert response_data["msg"] == detail



