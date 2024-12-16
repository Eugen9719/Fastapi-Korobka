from sqlmodel import create_engine

from backend.core.config import settings



database_url = settings.database_url
engine = create_engine(database_url)

