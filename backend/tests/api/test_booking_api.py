import logging

import pytest
from datetime import timedelta

from backend.core import security
from backend.core.config import settings

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_create_200 = {"start_time": "2024-12-08T14:35:32.437Z", "end_time": "2024-12-08T15:35:32.437Z", "stadium_id": 2}
data_create_400_2 = {"start_time": "2024-08-04T09:33:42.502","end_time": "2024-08-04T15:33:42.502", "stadium_id": 2}
data_create_400_3 = {"start_time": "2024-11-13T14:35:32.437Z", "end_time": "2024-11-13T15:35:32.437Z", "stadium_id": 1}
data_create_400_4 = {"start_time": "2024-11-13T19:35:32.437Z", "end_time": "2024-11-13T15:35:32.437Z", "stadium_id": 2}


@pytest.mark.usefixtures("db", "client")
class TestBookingApi:
    @pytest.mark.parametrize("user_id, status, detail, data", [
        (1, 200, None, data_create_200),
        (2, 400, {"detail": "The selected time is already booked."}, data_create_400_2),
        (2, 400, {"detail": "The stadium is not active for booking."}, data_create_400_3),
        (2, 400, {"detail": "End time must be greater than start time."}, data_create_400_4),

    ])
    def test_create_booking(self, db, client, user_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = client.post(f"{settings.API_V1_STR}/booking/create", headers=headers, json=data)
        booking = response.json()
        logger.info(f"{booking}")

        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, booking_id,status, detail", [
        (1, 99, 404, {"detail": 'Объект не найден'}),
        (1, 2, 403, {"detail": "Только админ или создатель могут проводить операции"},),
        (4, 2, 200, None),

    ])
    def test_delete_booking(self, client, booking_id, user_id, status, detail):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = client.delete(f"{settings.API_V1_STR}/booking/delete/{booking_id}", headers=headers)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail


    def test_read_booking(self, client):
        token = security.create_access_token(2, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = client.get(f"{settings.API_V1_STR}/booking/read", headers=headers)
        assert response.status_code == 200

