from abc import ABC, abstractmethod

from backend.app.interface.base.i_base_repo import ICrudRepository
from backend.app.models import Wallet
from backend.app.models.wallet import WalletCreate, WalletUpdate


class IWalletRepository(ICrudRepository[Wallet, WalletCreate, WalletUpdate], ABC):
    pass
