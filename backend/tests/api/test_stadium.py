import logging

import pytest
from datetime import timedelta

from backend.core import security
from backend.core.config import settings

# Настраиваем логгирование для тестов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_data={"name": "string", "slug": "donbass", "address": "string", "description": "string",
                        "additional_info": "string", "price": 1, "country": "string", "city": "string"}
new_load_data ={"name": "string", "slug": "donbasssss", "address": "string", "description": "string",
                        "additional_info": "string", "price": 1, "country": "string", "city": "string"}
@pytest.mark.usefixtures("db", "client")
class TestStadiumApi:
    @pytest.mark.parametrize("user_id,status, detail, data", [
        (4, 400, {"detail": "This user not owner"}, load_data),
        (1, 200, None, new_load_data ),
        (1, 400, {"detail": "Slug already used"},load_data),

    ])
    def test_create_stadium(self, db, client, user_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}


        response = client.post(f"{settings.API_V1_STR}/stadium/create", headers=headers, json=data)
        stadium_data = response.json()

        # Выводим данные о созданном стадионе

        # logger.info(f"Очистка данных из таблиц перед выполнением модуля.{stadium_data}")
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (3, 1, 200, None, {"status": "added", "reason": None}),
        (3, 5, 404, {"detail": "Объект не найден"}, {"status": "added"}),
        # (3, 1, 422, {"detail": "Недопустимый статус"}, {"status": "INVALID_STATUS"}),

    ])
    def test_verification_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = client.patch(f"{settings.API_V1_STR}/stadium/verification/{stadium_id}", headers=headers, json=data)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id,stadium_id, status, detail, data", [
        (1, 1, 200, None, {"name": "string", "slug": "string", "address": "string", "description": "string",
                           "additional_info": "string", "price": 1, "country": "string", "city": "string"}),
        (1, 99, 404, {"detail": 'Объект не найден'},
         {"name": "string", "slug": "string", "address": "string", "description": "string",
          "additional_info": "string", "price": 1, "country": "string", "city": "string"}),
         (2, 1, 403, {"detail": "Только админ или создатель могут проводить операции"},
         {"name": "string", "slug": "string", "address": "string", "description": "string",
          "additional_info": "string", "price": 1, "country": "string", "city": "string"}),

    ])
    def test_update_stadium(self, db, client, user_id, stadium_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = client.put(f"{settings.API_V1_STR}/stadium/update/{stadium_id}", headers=headers, json=data)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail


    def test_get_stadiums(self, client):
        response = client.get(f"{settings.API_V1_STR}/stadium/all")
        assert response.status_code == 200

    @pytest.mark.parametrize("stadium_id,status, detail", [
        (99, 404, {"detail": 'Объект не найден'}),
        (1, 200, None),

    ])
    def test_get_stadium(self, client, stadium_id, status, detail):
        response = client.get(f"{settings.API_V1_STR}/stadium/detail/{stadium_id}")
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, stadium_id,status, detail", [
        (1, 99, 404, {"detail": 'Объект не найден'}),
        (2, 1, 403, {"detail": "Только админ или создатель могут проводить операции"},),
        (1, 3, 200, None),

    ])
    def test_delete_stadium(self, client, stadium_id, user_id, status, detail):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}
        response = client.delete(f"{settings.API_V1_STR}/stadium/delete/{stadium_id}", headers=headers)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail
