import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"  # Базовая строка API
    SECRET_KEY: str = "" # Генерация случайного секретного ключа
    ALGORITHM:str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # Время жизни токена доступа (8 дней)
    DOMAIN: str = "localhost"  # Домен приложения
    ENVIRONMENT: Literal["local", "test", "production"] = 'local'
    SERVER_HOST: str = 'http://127.0.0.1:8080'
    LOG_LEVEL: str = ""

    UPLOAD_DIRECTORY: str = "static/img"

    PROJECT_NAME: str = "Ecommerce Nest API"
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
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@localhost:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
            )
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SMTP_TLS: bool = True  # Настройка использования TLS для SMTP
    SMTP_SSL: bool = False  # Настройка использования SSL для SMTP
    SMTP_PORT: int = 587  # Порт для SMTP сервера
    SMTP_HOST: str = 'smtp.zoho.eu'  # Адрес SMTP сервера
    SMTP_USER: str = 'jekapidchenko@zohomail.eu'  # Пользователь SMTP
    SMTP_PASSWORD: str = 'Mars03051972'  # Пароль SMTP
    EMAILS_FROM_EMAIL: str = 'jekapidchenko@zohomail.eu'  # Email отправителя
    EMAILS_FROM_NAME: str | None = None  # Имя отправителя

    EMAIL_TEMPLATE_DIR: str = 'backend/templates/build'

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # Время жизни токена для сброса пароля
    EMAIL_TEST_USER: str = "test@example.com"  # Тестовый email

    FIRST_SUPERUSER: str = ""
    FIRST_SUPERUSER_PASSWORD: str = ""

    STRIPE_PUBLISHABLE_KEY: str = "pk_test_51QX1mzGCiqNsEAmeKrRy569Fv59zJ6GYbHobGuQaSLncsIVm4B6Qjq0NVcx4jCIOrZzjfWMAIWDX0D1HnOnHl6UI00thgmXqiv"
    STRIPE_SECRET_KEY:str =  "sk_test_51QX1mzGCiqNsEAmeIcANkoXbiP7LGndJvnNhzeVVdv0ltY42BmMgv4ud0UnlF7TZqCadrB5vva0zgGLlZGHkSAM700Gt7auVHJ"
    STRIPE_WEBHOOK_SECRET:str = "whsec_be8a107eca99f4c29dfbd72141a38bcacf336239b72f0eb68f2d955058747cd0"


settings = Settings()



