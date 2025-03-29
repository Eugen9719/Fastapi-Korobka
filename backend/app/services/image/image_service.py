
import logging
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.abstractions.repository import ModelType
from backend.app.abstractions.storage import ImageHandler

logger = logging.getLogger(__name__)
class CloudinaryImageHandler(ImageHandler):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def upload_image(self, db: AsyncSession, instance: ModelType, file: UploadFile) -> dict:

        if not file.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image")
        try:
            folder = f"{self.model.__tablename__.lower()}/id-{instance.id}"
            result = cloudinary.uploader.upload(file.file, folder=folder, use_filename=True)
            instance.image_url = result["secure_url"]
            await db.commit()
            await db.refresh(instance)
            return {"url": result["secure_url"], "public_id": result["public_id"]}
        except Exception as e:
            await db.rollback()
            logger.error(f"Image upload failed: {str(e)}")
            raise HTTPException(500, "Image upload failed")
        finally:
            await file.close()

    async def delete_old_image(self, db: AsyncSession, instance: ModelType) -> None:

        if instance.image_url:
            try:
                result = cloudinary.uploader.destroy(instance.image_url.split('/')[-1])
                if result.get('result') == 'ok':
                    instance.image_url = None
                    await db.commit()
            except Exception as e:
                logger.error(f"Ошибка удаления фото: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Ошибка удаления старого фото: {str(e)}")