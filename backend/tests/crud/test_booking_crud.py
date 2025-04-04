
import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.dependencies.repositories import user_repo, booking_repo
from backend.app.models.bookings import BookingCreate



@pytest.mark.run(order=1)
@pytest.mark.anyio
class TestCrudBooking:
    @pytest.mark.parametrize("expected_exception, status_code, detail, user_id, start_time, end_time, stadium_id", [
        (None, 200, None, 1, "2024-12-08 14:00:00", "2024-12-08 16:00:00", 2),
        (HTTPException, 400, {"detail": "The selected time is already booked."}, 2, "2024-08-04T09:33:00", "2024-08-04T15:33:00", 2),
        (HTTPException, 400, {"detail": "The stadium is not active for booking."}, 2, "2024-12-08 10:00:00", "2024-12-08 11:00:00", 1),
        (HTTPException, 400, {"detail": "End time must be greater than start time."}, 2, "2024-12-08 14:00:00", "2024-11-08 14:00:00",
         2),
    ])
    async def test_create_booking(self, db: AsyncSession, expected_exception, status_code, detail, user_id, start_time, end_time, stadium_id):

        user = await user_repo.get_or_404(db=db, id=user_id)
        create_schema = BookingCreate(
            start_time=start_time,
            end_time=end_time,
            stadium_id=stadium_id
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await booking_repo.create_booking(db=db, schema=create_schema, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail["detail"]
        else:
            await booking_repo.create_booking(db=db, schema=create_schema, user=user)

    async def test_delete_booking(self, db: AsyncSession, ):
        user = await user_repo.get_or_404(db=db, id=4)
        response = await booking_repo.cancel_booking(db, booking_id=3, user=user)
        # Проверяем результат
        assert response["msg"] == "Бронирование и связанные услуги успешно удалены"

        # Проверяем, что стадион больше не существует в базе
        with pytest.raises(HTTPException) as exc_info:
            await booking_repo.get_or_404(db=db, id=3)
        assert exc_info.value.status_code == 404
