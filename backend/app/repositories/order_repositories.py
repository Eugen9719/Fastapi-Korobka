import stripe
from fastapi import HTTPException

from sqlmodel import Session, select

from backend.app.models import Order, User, AdditionalService
from backend.app.models.bookings import BookingService
from backend.app.models.orders import OrderCreate, OrderUpdate, StatusEnum
from backend.app.repositories.base_repositories import BaseRepository
from backend.app.repositories.bookings_repositories import booking_repo


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    def create_order(self, db: Session, schema: OrderCreate, user: User):
        # Проверка на существующее бронирование
        booking = booking_repo.get_or_404(db=db, id=schema.booking_id)
        if self.get_by_filter(db, self.model.booking_id == booking.id):
            raise HTTPException(status_code=400, detail="Бронирование уже используется")
        self.check_current_user(current_user=user, model=booking)

        all_service_price = 0
        # # Если переданы услуги, добавляем их к букингу
        if schema.services:
            for service_data in schema.services:
                service = db.query(AdditionalService).filter_by(id=service_data.service_id).first()
                if not service:
                    raise HTTPException(status_code=404, detail=f"Service with ID {service_data.service_id} not found")

                all_service_price += (service.price * service_data.quantity)

                booking_service = BookingService(
                    booking_id=booking.id,
                    service_id=service_data.service_id,
                    quantity=service_data.quantity,
                    total_price=service.price * service_data.quantity
                )
                db.add(booking_service)
        # Рассчитываем общую стоимость
        total_price = booking.price + all_service_price

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
        # Проверяем статус заказа
        if order.status != StatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Only pending orders can be paid.")
        # Меняем статус заказа
        order.status = StatusEnum.COMPLETED
        self.save_db(db, order)
        return order

    def create_payment_session(self, db: Session, order_id: int, success_url: str, cancel_url: str):
        # Получение заказа
        order = self.get_or_404(db=db, id=order_id)
        if order.status != StatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Order must be pending to create a payment session.")

        # Формирование списка line_items для Stripe
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Заказ #{order.id} - {order.booking.stadium.name}",
                        "description": (
                            f"Бронирование с {order.booking.formatted_start_time} "
                            f"по {order.booking.formatted_end_time}"
                        ),

                    },
                    "unit_amount": int(order.booking.price * 100),  # Общая стоимость заказа в центах
                },
                "quantity": 1,
            },


        ]
        if order.booking.booking_services:
            # Добавление услуг из бронирования
            for service in order.booking.booking_services:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": service.service.name,  # Имя услуги
                            "description": service.service.description or "Описание услуги",  # Описание услуги
                            "images": ["https://example.com/image2.png"],  # Замените на реальный URL изображения
                        },
                        "unit_amount": int(service.service.price * 100),  # Стоимость услуги в центах
                    },
                    "quantity": service.quantity,  # Количество единиц услуги
                })

        # Создание Stripe-сессии
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"order_id": order.id},  # Метаданные для связи заказа со Stripe
        )

        return session.url



order_repo = OrderRepository(Order)
