from abc import ABC

from backend.app.interface.base.i_base_repo import ICrudRepository

from backend.app.models.wallet import  Transaction, TransactionCreate, TransactionUpdate


class ITransactionRepository(ICrudRepository[Transaction, TransactionCreate, TransactionUpdate], ABC):
    pass