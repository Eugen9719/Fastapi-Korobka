from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.interface.repositories.i_verification_repo import IVerifyRepository
from backend.app.interface.repositories.i_wallet_repo import IWalletRepository
from backend.app.interface.utils.i_password_service import IPasswordService
from backend.app.models.auth import VerificationCreate, VerificationOut
from backend.app.models.users import UserCreate, UserUpdateActive
from backend.app.models.wallet import WalletCreate
from backend.app.services.decorators import HttpExceptionWrapper
from backend.app.services.email.email_service import EmailService


class RegistrationService:
    """Сервис регистрации пользователей"""

    def __init__(self, user_repository: IUserRepository, verif_repository: IVerifyRepository,
                 email_service: EmailService, pass_service: IPasswordService,
                 wallet_repository:IWalletRepository
                 ):
        self.user_repository = user_repository
        self.verif_repository = verif_repository
        self.email_service = email_service
        self.pass_service = pass_service
        self.wallet_repository = wallet_repository

    @HttpExceptionWrapper
    async def register_user(self, schema: UserCreate, db: AsyncSession):
        existing_user = await self.user_repository.get_by_email(db, email=schema.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
        hashed_password = self.pass_service.hash_password(schema.password)
        user = await self.user_repository.create(db, schema=schema, hashed_password=hashed_password)
        await self.wallet_repository.create(db, schema=WalletCreate(user_id=user.id))
        verify = await self.verif_repository.create(db, schema=VerificationCreate(user_id=user.id))
        await self.email_service.send_verification_email(schema.email, schema.email, schema.password, verify.link)
        return {"msg": "Письмо с подтверждением отправлено"}

    @HttpExceptionWrapper
    async def verify_user(self, uuid: VerificationOut, db: AsyncSession):
        verify = await self.verif_repository.get(db, link=str(uuid.link))
        if not verify:
            raise HTTPException(status_code=404, detail="Verification failed")

        user = await self.user_repository.get_or_404(db=db, object_id=verify.user_id)
        update_data = {"is_active": True}
        user_update_schema = UserUpdateActive(**update_data)
        await self.user_repository.update(db, model=user, schema=user_update_schema.model_dump(exclude_unset=True))
        await self.verif_repository.remove(db, link=uuid.link)
        return {"msg": "Email успешно подтвержден"}
