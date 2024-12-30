from backend.core.config import settings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

database_url = settings.database_url

# синхронное подключение
# engine = create_engine(database_url)


# Создание асинхронного движка
engine: AsyncEngine = create_async_engine(database_url, echo=False)
