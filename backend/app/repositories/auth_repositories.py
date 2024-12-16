from backend.app.models.auth import Verification, VerificationCreate, VerificationOut
from backend.app.repositories.base_repositories import BaseRepository


class VerifyRepository(BaseRepository[Verification, VerificationCreate, VerificationOut]):
    pass


auth_repository = VerifyRepository(Verification)
