from backend.app.interface.repositories.i_verification_repo import IVerifyRepository
from backend.app.models import Verification
from backend.app.models.auth import VerificationCreate, VerificationOut
from backend.app.repositories.base_repositories import AsyncBaseRepository


class VerifyRepository(IVerifyRepository, AsyncBaseRepository[Verification, VerificationCreate, VerificationOut]):
    def __init__(self):
        super().__init__(Verification)
