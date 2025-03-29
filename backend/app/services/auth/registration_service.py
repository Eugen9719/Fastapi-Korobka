from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.abstractions.services import IPasswordService
from backend.app.models.auth import VerificationCreate, VerificationOut
from backend.app.models.users import UserCreate, UserUpdateActive
from backend.app.repositories.user_repositories import UserRepository
from backend.app.repositories.verification_repository import VerifyRepository
from backend.app.services.email.email_service import EmailService


class RegistrationService:
    """Сервис регистрации пользователей"""

    def __init__(self, user_repository: UserRepository, verif_repository: VerifyRepository, email_service: EmailService, pass_service: IPasswordService,):
        self.user_repository = user_repository
        self.verif_repository = verif_repository
        self.email_service = email_service
        self.pass_service = pass_service

    async def register_user(self, new_user: UserCreate, db: AsyncSession):
        existing_user = await self.user_repository.get_by_email(db, email=new_user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
        hashed_password = self.pass_service.hash_password(new_user.password)
        user = await self.user_repository.create_user(db, schema=new_user, hashed_password=hashed_password)
        verify = await self.verif_repository.create(db, schema=VerificationCreate(user_id=user.id))
        await self.email_service.send_verification_email(new_user.email, new_user.email, new_user.password, verify.link)
        return {"msg": "Письмо с подтверждением отправлено"}

    async def verify_user(self, uuid: VerificationOut, db: AsyncSession):
        verify = await self.verif_repository.get(db, link=uuid.link)
        if not verify:
            raise HTTPException(status_code=404, detail="Verification failed")

        user = await self.user_repository.get_or_404(db=db, id=verify.user_id)
        update_data = {"is_active": True}
        user_update_schema = UserUpdateActive(**update_data)
        await self.user_repository.update(db, model=user, schema=user_update_schema.model_dump(exclude_unset=True))
        await self.verif_repository.remove(db, link=uuid.link)
        return {"msg": "Email успешно подтвержден"}
