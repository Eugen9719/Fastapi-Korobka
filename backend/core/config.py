from typing import Literal

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"  # Базовая строка API
    SECRET_KEY: str = ""  # Генерация случайного секретного ключа
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60 * 24 * 7 # Время жизни токена доступа (7 дней)
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

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    EMAIL_TEMPLATE_DIR: str = 'backend/templates/build'

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # Время жизни токена для сброса пароля

    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    SENTRY_DNS: str | None = None

    CLOUD_NAME: str | None = None
    CLOUD_API_KEY: str | None = None
    CLOUD_API_SECRET: str | None = None

    password_reset_jwt_subject: str = 'present'


settings = Settings()
print(settings.database_url)
