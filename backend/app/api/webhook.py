import stripe
from fastapi import APIRouter, Request, HTTPException

from backend.app.dependencies.service_factory import service_factory
from backend.app.models.bookings import StatusBooking
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.config import settings
from backend.core.db import SessionDep, TransactionSessionDep

webhook_router = APIRouter()


import logging

logger = logging.getLogger(__name__)

@webhook_router.post('/webhook/stripe')
@sentry_capture_exceptions
async def stripe_webhook(request: Request, db: TransactionSessionDep):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

    logger.info("🔔 Получен webhook от Stripe")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.info("✅ Событие Stripe успешно собрано")
    except ValueError as e:
        logger.error(f"❌ Неверный payload: {e}")
        raise HTTPException(status_code=400, detail="Неверный payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"❌ Ошибка проверки подписи: {e}")
        raise HTTPException(status_code=400, detail="Неверная подпись")

    logger.info(f"📦 Тип события: {event['type']}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(f"📨 Получена сессия: {session}")

        metadata = session.get("metadata", {})
        if not metadata:
            logger.warning("⚠️ В сессии отсутствуют metadata")
            return {"error": "Отсутствует metadata"}

        booking_id = metadata.get("booking_id")
        if not booking_id:
            logger.warning("⚠️ В metadata отсутствует booking_id")
            return {"error": "Отсутствует booking_id"}

        logger.info(f"🔎 Booking ID из metadata: {booking_id}")

        try:
            booking = await service_factory.booking_repo.get_or_404(db=db, object_id=int(booking_id))
            logger.info(f"✅ Найден booking: ID {booking.id}, статус {booking.status}")
        except Exception as e:
            logger.error(f"❌ Ошибка при получении booking: {e}")
            raise HTTPException(status_code=404, detail="Booking не найден")

        if booking.status == StatusBooking.PENDING:
            booking.status = StatusBooking.COMPLETED
            booking.stripe_payment_intent_id = session.get("payment_intent")

            try:
                await service_factory.booking_repo.save_db(db, booking)
                logger.info(f"💾 Статус booking обновлён на COMPLETED для ID {booking.id}")
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении booking: {e}")
                raise HTTPException(status_code=500, detail="Не удалось обновить booking")

    return {"success": True}

