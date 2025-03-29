from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"  # Базовая строка API
    SECRET_KEY: str = ""  # Генерация случайного секретного ключа
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # Время жизни токена доступа (8 дней)
    DOMAIN: str = "localhost"  # Домен приложения
    ENVIRONMENT: Literal["local", "test", "production"] = 'local'
    SERVER_HOST: str = 'http://127.0.0.1:8000'
    LOG_LEVEL: str = ""

    UPLOAD_DIRECTORY: str = "static/img"

    PROJECT_NAME: str = "KOROBKA API"
    POSTGRES_SERVER: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    TEST_POSTGRES_DB: str = ""

    @property
    def database_url(self):
        if self.ENVIRONMENT == "test":
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@localhost:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
            )
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@db:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SMTP_TLS: bool   # Настройка использования TLS для SMTP
    SMTP_SSL: bool   # Настройка использования SSL для SMTP
    SMTP_PORT: int   # Порт для SMTP сервера
    SMTP_HOST: str   # Адрес SMTP сервера
    SMTP_USER: str   # Пользователь SMTP
    SMTP_PASSWORD: str   # Пароль SMTP
    EMAILS_FROM_EMAIL: str  # Email отправителя
    EMAILS_FROM_NAME: str | None = None  # Имя отправителя

    EMAIL_TEMPLATE_DIR: str = 'backend/templates/build'

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # Время жизни токена для сброса пароля


    FIRST_SUPERUSER: str = ""
    FIRST_SUPERUSER_PASSWORD: str = ""

    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    SENTRY_DNS: str

    CLOUD_NAME: str
    CLOUD_API_KEY: str
    CLOUD_API_SECRET: str

    password_reset_jwt_subject: str = 'present'


settings = Settings()
