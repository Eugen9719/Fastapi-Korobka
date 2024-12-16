from sqlmodel import Session

from backend.app.models import Order, User
from backend.app.models.orders import OrderCreate, OrderUpdate
from backend.app.repositories.base_repositories import BaseRepository
from backend.app.repositories.bookings_repositories import booking_repo


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    def create_order(self, db: Session, schema: OrderCreate, user: User):
        booking = booking_repo.get_or_404(db=db, id=schema.booking_id)
        total_price = booking.price
        # Создаем бронирование через базовый метод
        return super().create(db=db, schema=schema, user_id=user.id, total_price=total_price)


order_repo = OrderRepository(Order)