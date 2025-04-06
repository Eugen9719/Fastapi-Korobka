import pytest
from backend.core.config import settings
from backend.tests.utils.utils import get_token_header

new_load_data = {"name": "string", "slug": "donbasssss", "address": "string", "description": "string",
                 "additional_info": "string", "price": 1, "country": "string", "city": "string"}


@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client", "test_data")
class TestStadiumApi:
    @pytest.mark.parametrize("user_id,status, detail, data", [
        (1, 200, None, new_load_data),
    ])
    async def test_create_stadium(self, db, client, user_id, status, detail, data):
        headers = get_token_header(user_id)
        response = await client.post(f"{settings.API_V1_STR}/stadium/create", headers=headers, json=data)
        assert response.status_code == status

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (3, 1, 200, None, {"status": "Added", "reason": None}),

    ])
    async def test_verification_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        headers = get_token_header(user_id)
        response = await client.patch(f"{settings.API_V1_STR}/stadium/approve/{stadium_id}", headers=headers,
                                      json=data)
        assert response.status_code == status

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (1, 1, 200, None, {"name": "string", "slug": "string", "address": "string", "description": "string",
                           "additional_info": "string", "price": 1, "country": "string", "city": "string"}),

    ])
    async def test_update_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        headers = get_token_header(user_id)
        response = await client.put(f"{settings.API_V1_STR}/stadium/update/{stadium_id}", headers=headers, json=data)
        assert response.status_code == status

    async def test_get_stadiums(self, client):
        response = await client.get(f"{settings.API_V1_STR}/stadium/all")
        assert response.status_code == 200

    @pytest.mark.parametrize("stadium_id,status, detail", [
        (1, 200, None),

    ])
    async def test_get_stadium(self, client, stadium_id, status, detail):
        response = await client.get(f"{settings.API_V1_STR}/stadium/detail/{stadium_id}")
        assert response.status_code == status

    @pytest.mark.parametrize("user_id, stadium_id,status, detail", [
        (1, 4, 200, None),

    ])
    async def test_delete_stadium(self,db,  client, stadium_id, user_id, status, detail):
        headers = get_token_header(user_id)
        response = await client.delete(f"{settings.API_V1_STR}/stadium/delete/{stadium_id}", headers=headers)
        assert response.status_code == status
