from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, and_

from backend.app.models import Message
from backend.app.models.chat import MessageCreate, MessageUpdate
from backend.app.repositories.base_repositories import AsyncBaseRepository


class MessageRepositories(AsyncBaseRepository[Message, MessageCreate, MessageUpdate]):
    async def get_messages_between_users(self, db: AsyncSession, user_id_1: int, user_id_2: int):
        """
        Асинхронно находит и возвращает все сообщения между двумя пользователями.

        Аргументы:
            user_id_1: ID первого пользователя.
            user_id_2: ID второго пользователя.

        Возвращает:
            Список сообщений между двумя пользователями.
        """

        query = select(self.model).filter(
            or_(
                and_(self.model.sender_id == user_id_1, self.model.recipient_id == user_id_2),
                and_(self.model.sender_id == user_id_2, self.model.recipient_id == user_id_1)
            )
        ).order_by(self.model.id)
        result = await db.execute(query)
        return result.scalars().all()


message_repo = MessageRepositories(Message)
