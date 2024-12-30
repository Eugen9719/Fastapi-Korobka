from datetime import timedelta

import pytest

from backend.core import security
from backend.core.config import settings


@pytest.mark.anyio
class TestReviewAPI:
    @pytest.mark.parametrize("user_id, stadium_id, status, detail, data", [
        (2, 2, 200, None, {"review": "gfghgf"}),
    ])
    async def test_add_review(self, db, client, user_id, stadium_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = await client.post(f"{settings.API_V1_STR}/add-review/{stadium_id}", headers=headers, json=data)

        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, review_id, status, detail, data", [
        (4, 2, 200, None, {"review": "gfghgf"}),
    ])
    async def test_update_review(self, db, client, user_id, review_id, status, detail, data):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = await client.put(f"{settings.API_V1_STR}/update_review/{review_id}", headers=headers, json=data)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail

    @pytest.mark.parametrize("user_id, review_id, status, detail, ", [
        (2, 3, 200, None),
    ])
    async def test_delete_review(self, db, client, user_id, review_id, status, detail):
        token = security.create_access_token(user_id, expires_delta=timedelta(minutes=10))
        headers = {"Authorization": f"Bearer {str(token)}"}

        response = await client.delete(f"{settings.API_V1_STR}/delete_review/{review_id}", headers=headers)
        assert response.status_code == status
        if response.status_code != 200:
            assert response.json() == detail
