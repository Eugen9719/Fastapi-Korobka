import logging

import pytest
from datetime import timedelta

from backend.core import security
from backend.core.config import settings

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.run(order=2)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "client")
class TestBookingApi:

    async def test_create_booking(self, db, client):
        token = security.create_access_token(1, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        data = {
            "start_time": "2024-08-08T09:33:00",
            "end_time": "2024-08-08T15:33:00",
            "stadium_id": 2
        }
        response = await client.post(f"{settings.API_V1_STR}/booking/create", headers=headers, json=data)
        assert response.status_code == 200

    async def test_delete_booking(self, client):
        token = security.create_access_token(4, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.delete(f"{settings.API_V1_STR}/booking/delete/{2}", headers=headers)
        assert response.status_code == 200

    async def test_read_booking(self, client):
        token = security.create_access_token(2, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = await client.get(f"{settings.API_V1_STR}/booking/read", headers=headers)
        assert response.status_code == 200
