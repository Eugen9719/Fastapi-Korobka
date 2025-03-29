
from datetime import datetime
from decimal import Decimal

# Функция для преобразования неподдерживаемых типов
def serialize_datetime(obj):
    """Конвертирует datetime и Decimal в строку/число для JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()  # Преобразуем datetime в строку
    if isinstance(obj, Decimal):
        return float(obj)  # Преобразуем Decimal в float
    raise TypeError(f"Type {type(obj)} is not serializable")

# Функция для преобразования данных обратно в объекты
def deserialize_datetime(data):
    """Конвертирует строки обратно в datetime и Decimal."""
    for item in data["items"]:
        if "created_at" in item:
            item["created_at"] = datetime.fromisoformat(item["created_at"])
        if "updated_at" in item:
            item["updated_at"] = datetime.fromisoformat(item["updated_at"])
        for key, value in item.items():
            if isinstance(value, str) and value.replace(".", "", 1).isdigit():
                item[key] = Decimal(value)  # Преобразуем строку обратно в Decimal
    return data