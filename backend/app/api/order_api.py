import stripe
from fastapi import APIRouter

from ..base.auth.permissions import CurrentUser
from ..base.utils.deps import SessionDep

from ..models.orders import OrderRead, OrderCreate

from ..repositories.order_repositories import order_repo
from ...core.config import settings

order_router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY


@order_router.post('/create', response_model=OrderRead)
async def create_order(schema: OrderCreate, db: SessionDep, user: CurrentUser):
    return await order_repo.create_order(db=db, schema=schema, user=user)


# @order_router.put('/update/{order_id}', response_model=OrderRead)
# def update_order(schema: OrderUpdate, order_id: int, db: SessionDep, current_user: CurrentUser):
#     return order_repo.update_order(db=db, order_id=order_id, schema=schema, user=current_user)
#
# @order_router.delete("/delete/{order_id}")
# def delete_booking(db: SessionDep, current_user: CurrentUser, order_id: int) -> Msg:
#     order = order_repo.get_or_404(db, id=order_id)
#     order_repo.check_current_user_or_admin(current_user=current_user, model=order)
#     order_repo.remove(db, id=order.id)
#     return Msg(msg="booking deleted successfully")

@order_router.put('/cancel/{order_id}', response_model=OrderRead)
async def cancel_order(order_id: int, db: SessionDep, user: CurrentUser):
    return await order_repo.cancel_order(db=db, order_id=order_id, user=user)


@order_router.put('/pay/{order_id}', response_model=OrderRead)
async def pay_order(order_id: int, db: SessionDep):
    return await order_repo.mark_as_paid(db=db, order_id=order_id)


@order_router.post('/pay/{order_id}', response_model=dict)
async def create_payment_session(order_id: int, db: SessionDep, user: CurrentUser):
    success_url = "http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "http://localhost:8000/cancel"
    payment_url = await order_repo.create_payment_session(db=db, order_id=order_id, success_url=success_url,
                                                          cancel_url=cancel_url)
    return {"payment_url": payment_url}
