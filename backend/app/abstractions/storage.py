from abc import ABC, abstractmethod

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.abstractions.repository import ModelType


# Интерфейс для работы с изображениями
class ImageHandler(ABC):
    @abstractmethod
    async def upload_image(self, db: AsyncSession, instance: ModelType, file: UploadFile) -> dict:
        pass

    @abstractmethod
    async def delete_old_image(self, db: AsyncSession, instance: ModelType) -> None:
        pass