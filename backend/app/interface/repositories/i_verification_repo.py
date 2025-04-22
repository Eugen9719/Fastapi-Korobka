from abc import ABC

from backend.app.interface.base.i_base_repo import IReadRepository, ICrudRepository
from backend.app.models import Verification
from backend.app.models.auth import VerificationCreate, VerificationOut


class IVerifyRepository(IReadRepository[Verification],
                        ICrudRepository[Verification, VerificationCreate, VerificationOut], ABC):
    pass
