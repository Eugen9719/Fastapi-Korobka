import stripe
from fastapi import APIRouter, Request, HTTPException

from backend.app.dependencies.service_factory import service_factory
from backend.app.models.bookings import StatusBooking
from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.config import settings
from backend.core.db import SessionDep

webhook_router = APIRouter()


@webhook_router.post('/webhook/stripe')
@sentry_capture_exceptions
async def stripe_webhook(request: Request, db: SessionDep):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event= None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Обработка события успешной оплаты
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session["metadata"]["booking_id"]

        booking = await service_factory.booking_repo.get_or_404(db=db, object_id=int(booking_id))
        if booking.status == StatusBooking.PENDING:
            booking.status = StatusBooking.COMPLETED
            booking.stripe_payment_intent_id = session.get("payment_intent")
            await service_factory.booking_repo.save_db(db, booking)
    return {"success": True}

