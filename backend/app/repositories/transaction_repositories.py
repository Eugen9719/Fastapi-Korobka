from backend.app.interface.repositories.i_transaction_repo import ITransactionRepository
from backend.app.models import Transaction
from backend.app.models.wallet import TransactionCreate, TransactionUpdate
from backend.app.repositories.base_repositories import AsyncBaseRepository


class TransactionRepository(ITransactionRepository, AsyncBaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self):
        super().__init__(Transaction)
