from backend.app.models.auth import Verification, VerificationCreate, VerificationOut
from backend.app.repositories.base_repositories import AsyncBaseRepository


class VerifyRepository(AsyncBaseRepository[Verification, VerificationCreate, VerificationOut]):
    pass


auth_repo = VerifyRepository(Verification)
