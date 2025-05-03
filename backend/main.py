import logging
import cloudinary
import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.app import routers
from backend.app.dependencies.service_factory import service_factory

from backend.core.config import settings
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn=settings.SENTRY_DNS,
    integrations=[
        SqlalchemyIntegration(),  # Интеграция с SQLAlchemy
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),  # Логирование
    ],
    traces_sample_rate=1.0,  # Включение трассировки (для производительности)
)

# Инициализация FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    DEBUG=True
)


app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


@app.on_event("startup")
async def startup():
    await service_factory.redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    await service_factory.redis_client.disconnect()

# Подключение статики
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройки CORS
origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно ограничить доступ только к определенным доменам
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUD_NAME,
    api_key=settings.CLOUD_API_KEY,
    api_secret=settings.CLOUD_API_SECRET,
    secure=True
)










# Подключение маршрутов
app.include_router(routers.api_router, prefix=settings.API_V1_STR)













######################################## Admin #########################################################################

# admin = Admin(app, engine, authentication_backend=authentication_backend)
#
# admin.add_view(UserAdmin)
