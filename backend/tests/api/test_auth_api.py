import logging
import uuid
from datetime import datetime

import pytest
from unittest.mock import patch, ANY

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from backend.app.models.auth import VerificationCreate
from backend.app.repositories.auth_repositories import auth_repo
from backend.app.services.auth.auth_service import generate_password_reset_token
from backend.tests.utils.utils import random_lower_string, random_email

from backend.core.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(test_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@pytest.mark.run(order=2)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client", "create_user")
class TestAuthUser:

    @patch("backend.app.services.auth.auth_service.send_new_account_email")
    async def test_registration_new_user(self, mock_send_email, client: AsyncClient, db: AsyncSession):
        """Тест регистрации нового пользователя"""
        start_time = datetime.now()
        logger.info(f"Начало теста: {self.__class__.__name__}.{self.test_registration_new_user.__name__}")

        try:

            email = random_email()
            password = random_lower_string()

            login_data = {
                "email": email,
                "password": password,
            }
            response = await client.post(f"{settings.API_V1_STR}/auth/registration", json=login_data)
            assert response.status_code == 200

            # Отправка повторного запроса с теми же данными
            response = await client.post(f"{settings.API_V1_STR}/auth/registration", json=login_data)
            assert response.status_code == 400
            assert response.json()["detail"] == "Email уже зарегистрирован"

            # Проверка вызова функции отправки письма
            logger.info("Проверка вызова функции отправки письма.")
            mock_send_email.assert_called_once_with(ANY, ANY, ANY, ANY)

            logger.info(f"Тест успешно завершен: {self.__class__.__name__}.{self.test_registration_new_user.__name__}")
        finally:
            # Время выполнения теста
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.info(f"Время выполнения теста: {execution_time:.3f} сек.")

    @pytest.mark.parametrize(
        "email, password, status_code, detail",
        [("vendor@gmail.com", "mars03051972", 200, None),
         ])
    async def test_login_access_token(self, db: AsyncSession, client: AsyncClient, email, password, status_code,
                                      detail):
        """Тест на получение access token с различными комбинациями email и пароля."""
        start_time = datetime.now()
        logger.info(
            f"Запуск теста {self.test_login_access_token.__name__} для: {email}, password: {password}")
        try:
            login_data = {
                "username": email,
                "password": password,
            }

            response = await client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

            # Проверка ответа
            assert response.status_code == status_code
            if response.status_code == 200:
                tokens = response.json()
                assert "access_token" in tokens
                assert tokens["access_token"]
                assert tokens["token_type"] == "bearer"
            else:
                assert response.json() == detail

            logger.info(f"Завершение теста для email: {email}")
        finally:
            # Время выполнения теста
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.info(f"Время выполнения теста: {execution_time:.3f} сек.")

    async def test_confirm_email_success(self, db: Session, client: AsyncClient, create_user) -> None:
        """Тест успешного подтверждения email"""
        logger.info(f"Начало теста: {self.test_confirm_email_success.__name__}")
        user, _ = await create_user()
        # Создаем верификационный объект для подтверждения
        verification = await auth_repo.create(db, schema=VerificationCreate(user_id=user.id))
        # Отправляем POST запрос на подтверждение email
        response = await client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": str(verification.link)})
        # Проверяем, что статус ответа 200 и содержится соответствующее сообщение
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"msg": "Email successfully verified"}
        logger.info(f"Завершение теста: {self.__class__.__name__}.{self.test_confirm_email_success.__name__}")

    async def test_confirm_email_failure(self, db: Session, client: AsyncClient) -> None:
        """Тест неудачного подтверждения email"""
        logger.info(f"Начало теста: {self.test_confirm_email_failure.__name__}")
        # Отправляем POST запрос с неверным UUID
        invalid_uuid = str(uuid.uuid4())
        response = await client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": invalid_uuid})

        # Проверяем, что статус ответа 404 и содержится соответствующее сообщение об ошибке
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Verification failed"}
        logger.info(f"Завершение теста: {self.test_confirm_email_failure.__name__}")

    async def test_password_recovery(self, db: Session, client: AsyncClient):
        email = "customer@gmail.com"
        response = await client.post(f"{settings.API_V1_STR}/auth/password-recovery/{email}", )
        # Проверка ответа
        assert response.status_code == 200
        assert response.json() == {"msg": "Password recovery email sent"}

    # async def test_reset_password(self, db: Session, client: AsyncClient):
    #     email = "customer@gmail.com"
    #     password = "Mars03051972"
    #     # Создаем токен для теста
    #     password_reset_token = generate_password_reset_token(email)
    #
    #     # Эмуляция запроса на изменение пароля
    #     response = await client.post(
    #         f"{settings.API_V1_STR}/auth/reset_password",data={"token": password_reset_token, "new_password": password}
    #     )
    #
    #     # Проверка статуса ответа
    #     assert response.status_code == 200

        # # Проверка содержимого ответа
        # response_data = response.json()
        # assert response_data["msg"] == "Password updated successfully"
