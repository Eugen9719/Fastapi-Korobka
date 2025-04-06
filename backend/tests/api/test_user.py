import pytest
import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.tests.utils.utils import get_token_header

logger = logging.getLogger(__name__)


@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client", "test_data")
class TestUserApi:
    async def test_get_user_me(self, db: AsyncSession, client: AsyncClient):
        headers = get_token_header(user_id=1)
        response = await client.get(f"{settings.API_V1_STR}/user/me", headers=headers)
        assert response.status_code == 200

    @pytest.mark.parametrize("user_id,r_user_id, status, detail", [
        (3, 1, 200, None),
        (1, 1, 403, {'detail': 'Требуются права администратора'})
    ])
    async def test_get_user_by_id(self, db, client, user_id, r_user_id, status, detail):

        headers = get_token_header(user_id)

        response = await client.get(f"{settings.API_V1_STR}/user/{r_user_id}", headers=headers)

        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, email, status, detail", [
        (1, "user1@example.com", 200, None)
    ])
    async def test_update_user_me(self, db, client, user_id, email, status, detail):
        # Создание токена доступа
        headers = get_token_header(user_id)

        # Данные для обновления
        update_data = {
            "email": email,
            "first_name": "string",
            "last_name": "string",
            "avatar": "string"
        }

        response = await client.patch(f"{settings.API_V1_STR}/user/me", headers=headers, json=update_data)

        # Проверки
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, password, new_password, status, detail", [
        (1, "mars03051972", "stringst2s", 200, None),

    ])
    async def test_update_password_me(self, db, client, user_id, password, new_password, status, detail):
        headers = get_token_header(user_id)
        update_data = {

            "current_password": password,
            "new_password": new_password

        }
        response = await client.patch(f"{settings.API_V1_STR}/user/me/password", headers=headers, json=update_data)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    async def test_read_users_admin(self, client):
        headers = get_token_header(user_id=3)
        response = await client.get(f"{settings.API_V1_STR}/user/all_user", headers=headers)
        assert response.status_code == 200

    # async def test_upload_avatar(self, client, db):
    #     token = security.create_access_token(1, expires_delta=timedelta(minutes=10))
    #     headers = {"Authorization": f"Bearer {str(token)}"}
    #     # Создание фала для теста
    #     file_content = b"fake image content"  # Можете заменить на реальный контент файла
    #     file = io.BytesIO(file_content)
    #     file.name = "avatar.jpg"  # Устанавливаем имя файла
    #
    #     # Эмуляция запроса на загрузку аватара
    #     response = await client.patch(
    #         f"{settings.API_V1_STR}/user/upload-avatar",
    #         files={"file": ("avatar.jpg", file, "image/jpeg")}, headers=headers  # Загружаем файл
    #     )
    #
    #     # Проверка статуса ответа
    #     assert response.status_code == 200  # Убедитесь, что ожидаете 200 OK

    @pytest.mark.parametrize("admin_id, user_id,   status, detail", [
        (3, 1, 200, None),

    ])
    async def test_delete_user(self, client, admin_id, user_id, status, detail):
        headers = get_token_header(user_id=admin_id)
        response = await client.delete(f"{settings.API_V1_STR}/user/delete/{user_id}", headers=headers)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail
