from backend.app.interface.repositories.i_wallet_repo import IWalletRepository
from backend.app.models import Wallet
from backend.app.models.wallet import WalletCreate, WalletUpdate
from backend.app.repositories.base_repositories import AsyncBaseRepository


class WalletRepository(IWalletRepository, AsyncBaseRepository[Wallet, WalletCreate, WalletUpdate]):
    def __init__(self):
        super().__init__(Wallet)


