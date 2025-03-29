import logging
from typing import List, Dict

from fastapi import APIRouter

from backend.app.dependencies.auth_dep import CurrentUser
from backend.app.dependencies.repositories import message_repo
from backend.app.models.chat import MessageRead, MessageCreate
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

from backend.app.services.decorators import sentry_capture_exceptions
from backend.core.db import SessionDep

message_router = APIRouter()


@message_router.get("/messages/{user_id}", response_model=List[MessageRead])
@sentry_capture_exceptions
async def get_messages(db: SessionDep, user_id: int, current_user: CurrentUser):
    return await message_repo.get_messages_between_users(db=db, user_id_1=user_id, user_id_2=current_user.id) or []


logger = logging.getLogger(__name__)

@message_router.post("/messages", response_model=MessageRead)
@sentry_capture_exceptions
async def send_message(db: SessionDep, schema: MessageCreate, current_user: CurrentUser):
    # Создаем сообщение
    message = await message_repo.create(db=db, schema=schema, sender_id=current_user.id)

    # Подготовка данных для уведомления
    message_data = {
        'sender_id': current_user.id,
        'recipient_id': schema.recipient_id,
        'content': schema.content,
    }

    # Уведомление через WebSocket
    await notify_user(schema.recipient_id, message_data)
    await notify_user(current_user.id, message_data)

    # Возвращаем объект с данными сообщения
    return MessageRead(
        id=message.id,
        recipient_id=schema.recipient_id,
        content=schema.content,
        sender_id=current_user.id
    )


# Активные WebSocket-подключения: {user_id: websocket}
active_connections: Dict[int, WebSocket] = {}


# Функция для отправки сообщения пользователю, если он подключен
async def notify_user(user_id: int, message: dict):
    """Отправить сообщение пользователю, если он подключен."""
    if user_id in active_connections:
        websocket = active_connections[user_id]
        # Отправляем сообщение в формате JSON
        await websocket.send_json(message)


# WebSocket эндпоинт для соединений
@message_router.websocket("/ws/{user_id}")
@sentry_capture_exceptions
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # Принимаем WebSocket-соединение
    await websocket.accept()
    # Сохраняем активное соединение для пользователя
    active_connections[user_id] = websocket
    try:
        while True:
            # Просто поддерживаем соединение активным (1 секунда паузы)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Удаляем пользователя из активных соединений при отключении
        active_connections.pop(user_id, None)