import logging

import pytest
from datetime import timedelta

from backend.app.repositories.stadiums_repositories import stadium_repo
from backend.core import security
from backend.core.config import settings

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

new_load_data = {"name": "string", "slug": "donbasssss", "address": "string", "description": "string",
                 "additional_info": "string", "price": 1, "country": "string", "city": "string"}

@pytest.mark.run(order=2)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client")
class TestStadiumApi:
    @pytest.mark.parametrize("user_id,status, detail, data", [
        (1, 200, None, new_load_data),
    ])
    async def test_create_stadium(self, db, client, user_id, status, detail, data):
        stadiums = await stadium_repo.get_many(db=db)
        for stadium in stadiums:
            logger.info(f"Stadium: {stadium.id}")
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.post(f"{settings.API_V1_STR}/stadium/create", headers=headers, json=data)
        after_stadiums = await stadium_repo.get_many(db=db)
        for stadium1 in after_stadiums:
            logger.info(f"after test  Stadium: {stadium1.id}")
        assert response.status_code == status

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (3, 1, 200, None, {"status": "added", "reason": None}),

    ])
    async def test_verification_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.patch(f"{settings.API_V1_STR}/stadium/verification/{stadium_id}", headers=headers,
                                      json=data)
        assert response.status_code == status

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (1, 1, 200, None, {"name": "string", "slug": "string", "address": "string", "description": "string",
                           "additional_info": "string", "price": 1, "country": "string", "city": "string"}),

    ])
    async def test_update_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
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
        stadiums = await stadium_repo.get_many(db=db)
        for stadium in stadiums:
            logger.info(f"Stadium: {stadium.id}")
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.delete(f"{settings.API_V1_STR}/stadium/delete/{stadium_id}", headers=headers)
        assert response.status_code == status
