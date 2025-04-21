import logging
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.app.dependencies.service_factory import service_factory
from backend.app.models.auth import VerificationCreate
from backend.app.models.users import UserCreate
from backend.core.config import settings
from backend.tests.utils.utils import random_email, random_lower_string

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(test_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client", "test_data")
class TestAuthUser:

    @pytest.mark.parametrize(
        "email, password, status_code, detail",
        [("vendor1@gmail.com", "mars03051972", 200, None),
         ("vendor134324@gmail.com", "mars03051972", 400, {'detail': 'Incorrect email or password'}),
         ])
    async def test_login_access_token(self, db: AsyncSession, client: AsyncClient, email, password, status_code,
                                      detail):

        login_data = {
            "username": email,
            "password": password,
        }

        response = await client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

        assert response.status_code == status_code
        if response.status_code == 200:
            tokens = response.json()
            assert "access_token" in tokens
            assert tokens["access_token"]
            assert tokens["token_type"] == "bearer"
        else:
            assert response.json() == detail

        logger.info(f"Завершение теста для email: {email}")

    async def test_confirm_email_success(self, db: AsyncSession, client: AsyncClient) -> None:
        email = random_email()
        password = random_lower_string()
        user = await service_factory.user_repo.create(
            db,
            schema=UserCreate(email=email, password=password),
            hashed_password=service_factory.password_service.hash_password(password)
        )

        verification = await service_factory.verify_repo.create(db, schema=VerificationCreate(user_id=user.id))
        await db.commit()
        await db.refresh(verification)

        # 4. Отправляем запрос
        response = await client.post(
            f"{settings.API_V1_STR}/auth/confirm_email",
            json={
                "link": verification.link
            }
        )

        # 5. Проверяем результат
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"msg": "Email успешно подтвержден"}  # Обратите внимание на точное сообщение

        logger.info(f"Тест успешно завершен")

    async def test_confirm_email_failure(self, db: AsyncSession, client: AsyncClient) -> None:
        """Тест неудачного подтверждения email"""
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

    async def test_reset_password(self, db: AsyncSession, client: AsyncClient):
        email = "customer@gmail.com"
        password = "Mars03051972"
        # Создаем токен для теста
        password_reset_token = service_factory.password_service.generate_password_reset_token(email)

        # Эмуляция запроса на изменение пароля
        response = await client.post(
            f"{settings.API_V1_STR}/auth/reset_password", json={"token": password_reset_token, "new_password": password}
        )
        # Проверка статуса ответа
        assert response.status_code == 200
        # Проверка содержимого ответа
        response_data = response.json()
        assert response_data["msg"] == "Пароль успешно изменен"
