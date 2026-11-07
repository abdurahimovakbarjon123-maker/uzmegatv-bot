from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.database.session import async_session


class DatabaseMiddleware(BaseMiddleware):
    """
    Har bir kelgan so'rov (Message, CallbackQuery) uchun
    AsyncSession yaratadi va handlerga uzatadi.
    """

    def __init__(self, session_pool: async_sessionmaker = async_session) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            try:
                data["session"] = session
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
