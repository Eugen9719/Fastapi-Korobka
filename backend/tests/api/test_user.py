
import pytest
from datetime import timedelta
from httpx import AsyncClient
from sqlmodel import Session
from backend.core import security
from backend.core.config import settings



@pytest.mark.run(order=2)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client")
class TestUserApi:
    async def test_get_user_me(self, db: Session, client: AsyncClient):

        token = security.create_access_token(1, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.get(f"{settings.API_V1_STR}/user/me", headers=headers)
        assert response.status_code == 200

    @pytest.mark.parametrize("user_id,r_user_id, status, detail", [
        (1, 1, 200, None),
    ])
    async def test_get_user_by_id(self, db, client, user_id, r_user_id, status, detail):

        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = await client.get(f"{settings.API_V1_STR}/user/{r_user_id}", headers=headers)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, email, status, detail", [
        (1, "user1@example.com", 200, None)
    ])
    async def test_update_user_me(self, db, client, user_id, email, status, detail):
        # Создание токена доступа
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

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
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        update_data = {

            "current_password": password,
            "new_password": new_password

        }
        response = await client.patch(f"{settings.API_V1_STR}/user/me/password", headers=headers, json=update_data)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    # async def test_read_users_admin(self, client):
    #     token = security.create_access_token(1, expires_delta=timedelta(minutes=10))
    #     headers = {"Authorization": f"Bearer {str(token)}"}
    #     response = await client.get(f"{settings.API_V1_STR}/user/", headers=headers)
    #     assert response.status_code == 200




    # @pytest.mark.parametrize("admin_id, user_id,   status, detail", [
    #     (3, 1, 200, None),
    #
    # ])
    # async def test_delete_user(self, client, admin_id, user_id, status, detail):
    #     token = security.create_access_token(admin_id, expires_delta=timedelta(minutes=10))
    #     headers = {"Authorization": f"Bearer {str(token)}"}
    #     response = await client.delete(f"{settings.API_V1_STR}/user/delete/{user_id}", headers=headers)
    #     assert response.status_code == status
    #     if response.status_code != 200:
    #         assert response.json() == detail
