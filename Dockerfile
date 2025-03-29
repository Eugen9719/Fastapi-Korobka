
FROM python:3.11

# Устанавливаем переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установим рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы из локальной системы в контейнер
COPY requirements.txt /app/requirements.txt
COPY backend /app/backend
COPY static /app/static
COPY .env /app/.env
COPY pytest.ini /app/pytest.ini
COPY initial_data.py /app/initial_data.py

# Установим зависимости
RUN pip install  -r requirements.txt

# Убедимся, что файлы и директории правильные
RUN ls /app

# Экспонируем порт, на котором будет работать FastAPI
EXPOSE 8000

# Запускаем сервер FastAPI с использованием Uvicorn
CMD ["uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
