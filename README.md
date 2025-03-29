# Korobka



для картинок установлен pip3 install cloudinary

pip install pytest-xdist


# ⚽ Korobka - Система бронирования футбольных полей

[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green)](https://fastapi.tiangolo.com/) 
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/) 
[![JWT Auth](https://img.shields.io/badge/Auth-JWT-orange)](https://jwt.io/) 
[![Stripe Payments](https://img.shields.io/badge/Payments-Stripe-blue)](https://stripe.com/) 
[![Sentry Monitoring](https://img.shields.io/badge/Monitoring-Sentry-orange)](https://sentry.io/)
[![Pytest](https://img.shields.io/badge/Testing-Pytest-purple)](https://docs.pytest.org/) 
[![Coverage](https://img.shields.io/badge/Coverage-90%25-brightgreen)](https://codecov.io/)

Платформа для бронирования футбольных полей с продвинутой системой управления стадионами и онлайн-оплатой.

## 🔐 Система аутентификации
- **Регистрация** с подтверждением email
- **JWT-авторизация** (токены доступа)
- **Две роли пользователей**:
  - 👥 Игроки - бронирование полей
  - 🏟️ Владельцы - управление стадионами

## 🏟️ Управление стадионами (для владельцев)
```mermaid
graph TD
    A[Создание стадиона,добавление сервисов, загрузка фото в Cloudinary]
    A --> C[Отправка на модерацию]
    C --> D{Одобрено админом?}
    D -->|Да| E[Стадион активен]
    D -->|Нет| F[Требуются правки]
 ```  
Полный CRUD для стадионов



Система верификации (только одобренные стадионы видны игрокам)

💎 Дополнительные услуги и отзывы

⚽ Доп. услуги к каждому стадиону (аренда мячей, форма и т.д.)


Фильтры бронирования:

    🕒 По времени доступности
    🌍 По городу/стране



💰 Система бронирования и оплаты
```mermaid

sequenceDiagram
    Игрок->>Система: Выбор стадиона и доп.услуг
    Система->>Stripe: Создание платежного интента
    Stripe-->>Система: Подтверждение оплаты
    Система->>Игрок: Подтверждение брони
```
Интеграция с Stripe API

Бронирование с привязкой дополнительных услуг

История заказов в личном кабинете

🧪 Тестирование
Полное покрытие API тестами (pytest)

Модульные и интеграционные тесты

🛠 **Технологии**

  - **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL
  - **Аутентификация**: JWT, OAuth2
  - **Хранение фото**: Cloudinary
  - **Кеширование**: Redis
  - **Мониторинг**: Sentry (ошибки и производительность)
  - **Оплата**: Stripe API
  - **Тестирование**: pytest, pytest-asyncio
  - **Инфраструктура**: Docker



🚀 Запуск проекта локально



### 1. Клонирование репозитория
```
git clone https://github.com/yourusername/footfield-pro.git
cd Korobka
```

## 2. Установка зависимостей pip 
```
pip install -r requirements.txt
  ```
## 3. Настройка Конфигурационного файла 
```
cp .env.example .env
# Отредактируйте .env файл согласно вашей конфигурации
```

## 4. Запуск тестов с отчетом о покрытии
```
pytest --cov=backend --cov-report=html 
 ```

## 5.  Запуск  сервера
```
uvicorn backend.main:app --reload
```
## 6. Документация
```
127.0.0.1:8000/docs
```



## 6. Сборка и запуск
``` 
docker-compose up --build
```

