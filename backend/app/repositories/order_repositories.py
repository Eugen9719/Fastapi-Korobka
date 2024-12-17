import stripe
from fastapi import HTTPException
from sqlalchemy.sql.functions import current_user
from sqlmodel import Session

from backend.app.models import Order, User
from backend.app.models.orders import OrderCreate, OrderUpdate, StatusEnum
from backend.app.repositories.base_repositories import BaseRepository
from backend.app.repositories.bookings_repositories import booking_repo


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    def create_order(self, db: Session, schema: OrderCreate, user: User):
        booking = booking_repo.get_or_404(db=db, id=schema.booking_id)
        total_price = booking.price
        # Создаем бронирование через базовый метод
        return super().create(db=db, schema=schema, user_id=user.id, total_price=total_price)

    def cancel_order(self, db: Session, order_id: int, user: User):
        # Получаем заказ
        order = self.get_or_404(db=db, id=order_id)
        # Проверяем, что только владелец может отменить заказ
        if order.user_id != user.id:
            raise HTTPException(status_code=403, detail="You are not allowed to cancel this order.")
        # Проверяем, что статус позволяет отмену
        if order.status != StatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Only pending orders can be canceled.")
        # Меняем статус и сохраняем
        order.status = StatusEnum.CANCELED
        self.save_db(db, order)
        return order

    def mark_as_paid(self, db: Session, order_id: int):
        # Получаем заказ
        order = self.get_or_404(db=db, id=order_id)
        # Проверяем, что статус позволяет оплату
        if order.status != StatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Only pending orders can be paid.")
        # Меняем статус на завершённый
        order.status = StatusEnum.COMPLETED
        self.save_db(db, order)
        return order

        # Метод для создания Stripe-сессии
    def create_payment_session(self, db: Session, order_id: int, success_url: str, cancel_url: str):
            order = self.get_or_404(db=db, id=order_id)
            if order.status != StatusEnum.PENDING:
                raise HTTPException(status_code=400, detail="Order must be pending to create a payment session.")

            # Создаём Stripe-сессию
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"Order #{order.id}"},
                            "unit_amount": order.total_price * 100,  # Stripe принимает сумму в центах
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"order_id": order.id},
            )
            return session.url


order_repo = OrderRepository(Order)
