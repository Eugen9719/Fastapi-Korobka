import stripe
from fastapi import APIRouter, Request, HTTPException

from backend.app.base.utils.deps import SessionDep
from backend.app.models.orders import StatusEnum
from backend.app.repositories.order_repositories import order_repo
from backend.core.config import settings

webhook_router = APIRouter()


@webhook_router.post('/webhook/stripe')
async def stripe_webhook(request: Request, db: SessionDep):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

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
        order_id = session["metadata"]["order_id"]

        order = order_repo.get_or_404(db=db, id=order_id)
        if order.status == StatusEnum.PENDING:
            order.status = StatusEnum.COMPLETED
            order_repo.save_db(db, order)

    return {"success": True}
