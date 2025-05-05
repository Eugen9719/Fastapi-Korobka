
import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.dependencies.service_factory import service_factory
from backend.app.models.bookings import BookingCreate



@pytest.mark.run(order=1)
@pytest.mark.anyio
@pytest.mark.usefixtures("db", "test_data")
class TestCrudBooking:
    @pytest.mark.parametrize("expected_exception, status_code, detail, user_id, start_time, end_time, stadium_id", [
        (None, 200, None, 1, "2024-12-08 14:00:00", "2024-12-08 16:00:00", 2),
        (HTTPException, 400, {"detail": "Этот промежуток времени уже забронирован."}, 2, "2024-08-04T09:33:00", "2024-08-04T15:33:00", 2),
        (HTTPException, 400, {"detail": "Этот стадион не активен для бронирования"}, 2, "2024-12-08 10:00:00", "2024-12-08 11:00:00", 1),
        (HTTPException, 400, {"detail": "Время окончания должно быть больше времени начала."}, 2, "2024-12-08 14:00:00", "2024-11-08 14:00:00",
         2),
    ])
    async def test_create_booking(self, db: AsyncSession, expected_exception, status_code, detail, user_id, start_time, end_time, stadium_id):

        user = await service_factory.user_repo.get_or_404(db=db, object_id=user_id)
        create_schema = BookingCreate(
            start_time=start_time,
            end_time=end_time,
            stadium_id=stadium_id
        )

        if expected_exception:
            with pytest.raises(expected_exception) as exc_info:
                await service_factory.booking_service.create_booking(db=db, schema=create_schema, user=user)
            assert exc_info.value.status_code == status_code
            assert exc_info.value.detail == detail["detail"]
        else:
            await service_factory.booking_service.create_booking(db=db, schema=create_schema, user=user)

    async def test_delete_booking(self, db: AsyncSession, ):
        user = await service_factory.user_repo.get_or_404(db=db, object_id=4)
        response = await service_factory.booking_service.delete_booking(db, booking_id=3, user=user)
        # Проверяем результат
        assert response["msg"] == "Бронирование и связанные услуги успешно удалены"

        # Проверяем, что стадион больше не существует в базе
        with pytest.raises(HTTPException) as exc_info:
            await service_factory.booking_repo.get_or_404(db=db, object_id=3)
        assert exc_info.value.status_code == 404
