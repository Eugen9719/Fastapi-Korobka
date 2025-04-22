from abc import ABC, abstractmethod
from typing import Optional


# Интерфейс для работы с паролями
class IPasswordService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        pass

    @abstractmethod
    def generate_password_reset_token(self, email: str):
        pass

    @abstractmethod
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        pass