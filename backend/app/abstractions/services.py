from abc import ABC, abstractmethod


# Интерфейс для работы с паролями
class IPasswordService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        pass