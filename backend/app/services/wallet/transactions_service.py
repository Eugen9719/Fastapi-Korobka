from backend.app.interface.repositories.i_transaction_repo import ITransactionRepository


class TransactionService:
    """Сервис управления пользователями"""

    def __init__(self, transaction_repository: ITransactionRepository):
        self.transaction_repository = transaction_repository