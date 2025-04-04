import logging
import uuid
from datetime import datetime
from unittest.mock import patch, ANY

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.app.dependencies.repositories import verify_repo, user_repo
from backend.app.dependencies.services import password_service
from backend.app.models.auth import VerificationCreate, Verification
from backend.app.models.users import UserCreate
from backend.app.services.email.email_service import EmailService
from backend.core.config import settings
from backend.tests.utils.utils import random_email, random_lower_string

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(test_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@pytest.mark.run(order=2)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client")
class TestAuthUser:

    @patch.object(EmailService, "send_verification_email")  # Правильный способ мокирования метода класса
    async def test_registration_new_user(self, mock_send_email, client: AsyncClient, db: AsyncSession):
        """Тест регистрации нового пользователя"""

        logger.info(f"Начало теста: {self.__class__.__name__}.{self.test_registration_new_user.__name__}")

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


    async def test_confirm_email_success(self, db: AsyncSession, client: AsyncClient) -> None:
        """Тест успешного подтверждения email"""
        logger.info(f"Начало теста: {self.test_confirm_email_success.__name__}")

        # 1. Создаем данные пользователя
        email = random_email()
        password = random_lower_string()

        # 2. Создаем Pydantic-модель для пользователя
        user_create = UserCreate(
            email=email,
            password=password  # Здесь передаем исходный пароль, не хеш
        )

        # 3. Хешируем пароль отдельно
        hashed_password = password_service.hash_password(password)

        # 4. Создаем пользователя
        user = await user_repo.create(
            db,
            schema=user_create,  # Передаем Pydantic-модель
            hashed_password=hashed_password
        )
        logger.info(f"Создан пользователь: ID={user.id}, Email={user.email}")

        # Создаем верификационный объект для подтверждения
        verification = await verify_repo.create(db, schema=VerificationCreate(user_id=user.id))
        logger.info(f"Ссылка для подтверждения: {verification.link}")

        # Получаем все записи из таблицы Verification
        result = await db.execute(select(Verification))
        verifications = result.scalars().all()  # Получаем все объекты Verification
        # Логируем содержимое
        logger.info(f"Все записи верификации в БД {verifications}")

        # Отправляем POST запрос на подтверждение email
        response = await client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": verification.link})
        # Проверяем, что статус ответа 200 и содержится соответствующее сообщение
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"msg": "Email successfully verified"}
        logger.info(f"Завершение теста: {self.__class__.__name__}.{self.test_confirm_email_success.__name__}")


    async def test_confirm_email_failure(self, db: AsyncSession, client: AsyncClient) -> None:
        """Тест неудачного подтверждения email"""
        logger.info(f"Начало теста: {self.test_confirm_email_failure.__name__}")
        # Отправляем POST запрос с неверным UUID
        invalid_uuid = str(uuid.uuid4())
        response = await client.post(f"{settings.API_V1_STR}/auth/confirm_email", json={"link": invalid_uuid})

        # Проверяем, что статус ответа 404 и содержится соответствующее сообщение об ошибке
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Verification failed"}
        logger.info(f"Завершение теста: {self.test_confirm_email_failure.__name__}")


    async def test_password_recovery(self, db: AsyncSession, client: AsyncClient):
        email = "customer@gmail.com"
        response = await client.post(f"{settings.API_V1_STR}/auth/password-recovery/{email}", )
        # Проверка ответа
        assert response.status_code == 200
        assert response.json() == {"msg": "Сброс пароля отправлен на email"}

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
