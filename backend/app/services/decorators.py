import logging
from functools import wraps
import sentry_sdk
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def sentry_capture_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise  # Оставляем HTTPException как есть
        except Exception as e:
            logger.exception(f"Ошибка в {func.__name__}")  # Логируем полную трассировку
            sentry_sdk.capture_exception(e)  # Отправляем в Sentry
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    return wrapper


# def invalidate_cache(prefix: str):
#     """
#     Декоратор для инвалидации кеша по указанному префиксу.
#     :param prefix: Префикс для удаления кеша (например, "stadiums:").
#     """
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(self, *args, **kwargs):
#             result = await func(self, *args, **kwargs)  # Выполняем оригинальную функцию
#             await redis_client.delete_cache_by_prefix(prefix)  # Инвалидация кеша
#             return result
#         return wrapper
#     return decorator




def HttpExceptionWrapper(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as http_exc:
            # Добавляем контекст для логов
            logger.warning(
                f"HTTP error {http_exc.status_code} в методе {func.__name__}: {http_exc.detail}",
                extra={
                    "status_code": http_exc.status_code,
                    "endpoint": func.__name__,
                    "detail": http_exc.detail
                }
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error в методе {func.__name__}: {str(e)}",
                exc_info=True,
                extra={
                    "endpoint": func.__name__,
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(500, "Internal server error")

    return wrapper
