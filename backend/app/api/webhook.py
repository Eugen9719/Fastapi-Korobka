import hmac
from decimal import Decimal
from hashlib import sha256

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlmodel import select

from backend.app.dependencies.service_factory import service_factory
from backend.app.models import Wallet, Transaction
from backend.app.models.bookings import StatusBooking
from backend.app.models.wallet import TransactionType, StatusPay
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.config import settings
from backend.core.db import TransactionSessionDep

webhook_router = APIRouter()

import logging

logger = logging.getLogger(__name__)


@webhook_router.post('/webhook/stripe')
@sentry_capture_exceptions
async def stripe_webhook(request: Request, db: TransactionSessionDep):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None
    logger.info("Получен webhook от Stripe")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.info("Событие Stripe успешно собрано")
    except ValueError as e:
        logger.error(f"Неверный payload: {e}")
        raise HTTPException(status_code=400, detail="Неверный payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Ошибка проверки подписи: {e}")
        raise HTTPException(status_code=400, detail="Неверная подпись")

    logger.info(f"📦 Тип события: {event['type']}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        booking_id = metadata.get("booking_id")
        if not booking_id:
            logger.warning("В metadata отсутствует booking_id")
            return {"error": "Отсутствует booking_id"}

        booking = await service_factory.booking_repo.get_or_404(db=db, object_id=int(booking_id))
        logger.info(f"✅ Найден services: ID {booking.id}, статус {booking.status}")

        if booking.status == StatusBooking.PENDING:
            booking.status = StatusBooking.COMPLETED
            booking.stripe_payment_intent_id = session.get("payment_intent")

            try:
                await service_factory.booking_repo.save_db(db, booking)
                logger.info(f"💾 Статус services обновлён на COMPLETED для ID {booking.id}")
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении services: {e}")
                raise HTTPException(status_code=500, detail="Не удалось обновить services")

            result = await db.execute(select(Wallet).where(Wallet.user_id == booking.owner_stadium))
            wallet = result.scalar_one_or_none()
            schema = Transaction(
                amount=booking.total_price * 0.9,  # Например, 90% от суммы бронирования
                type=TransactionType.DEPOSIT,
                status=StatusPay.COMPLETED,
                transaction_id=booking.stripe_payment_intent_id,
                wallet_id=wallet.id,
                extra_data={
                    "booking_id": booking.id,
                    "stadium_id": booking.stadium_id,
                    "description": "Начисление за бронирование"
                },
                signature=generate_signature(booking.id, wallet.id, secret_key=settings.SECRET_KEY)  # Опционально
            )
            transaction=await service_factory.transaction_repo.create(db, schema)


            wallet.balance += Decimal(transaction.amount)
            await service_factory.wallet_repo.save_db(db, wallet)

    return {"success": True}

def generate_signature(*args, secret_key: str) -> str:
    message = "|".join(str(arg) for arg in args)
    return hmac.new(secret_key.encode(), message.encode(), sha256).hexdigest()