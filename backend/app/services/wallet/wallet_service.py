import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.repositories.i_wallet_repo import IWalletRepository
from backend.app.models import Wallet, User
from backend.app.models.wallet import WalletCreate
from backend.app.services.utils_service.permission import PermissionService


class WalletService:
    """Сервис управления пользователями"""

    def __init__(self, wallet_repository: IWalletRepository, permission: PermissionService):
        self.wallet_repository = wallet_repository
        self.permission = permission

    async def create_wallet(self, db:AsyncSession,user:User) -> Wallet:
        schema = WalletCreate(
            user_id=user.id,
        )
        return await  self.wallet_repository.create(db=db, schema=schema)



    # @HttpExceptionWrapper
    # async def create_review(self, db: AsyncSession, schema: CreateReview, stadium_id: int, services: User):
    #     services = await self.stadium_repository.get_or_404(db=db, object_id=stadium_id)
    #     if await self.review_repository.check_duplicate_review(db=db, user_id=services.id, stadium_id=stadium_id):
    #         raise HTTPException(status_code=400, detail="Вы уже оставили отзыв для этого стадиона")
    #     services = await self.review_repository.create(db=db, schema=schema, stadium_id=services.id, user_id=services.id)
    #     logger.info(f"отзыв {services.id} успешно создан пользователем {services.id}")
    #     return services
    #
    # @HttpExceptionWrapper
    # async def update_review(self, db: AsyncSession, schema: UpdateReview, review_id: int, services: User):
    #     services = await self.review_repository.get_or_404(db=db, object_id=review_id)
    #     self.permission.check_owner_or_admin(current_user=services, model=services)
    #     services = await self.review_repository.update(db=db, model=services, schema=schema)
    #     logger.info(f"отзыв {review_id} успешно обновлен пользователем {services.id}")
    #     return services
    #
    # @HttpExceptionWrapper
    # async def delete_review(self, db: AsyncSession, services: User, review_id: int):
    #     services = await self.review_repository.get_or_404(db=db, object_id=review_id)
    #     self.permission.check_owner_or_admin(current_user=services, model=services)
    #     await self.review_repository.remove(db=db, id=services.id)
    #     logger.info(f"отзыв {review_id} успешно удален пользователем {services.id}")
    #     return Msg(msg="отзыв успешно удален")



