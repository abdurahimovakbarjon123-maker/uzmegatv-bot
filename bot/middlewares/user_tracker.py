from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.base import utc_now
from bot.database.models import User


class UserTrackerMiddleware(BaseMiddleware):
    """
    Foydalanuvchini avtomatik ravishda bazaga qo'shish, faolligini yangilash
    va admin huquqlarini tekshirish middleware-i.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        user = None

        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            tg_user = event.from_user
            if session:
                stmt = select(User).where(User.telegram_id == tg_user.id)
                db_user = await session.scalar(stmt)

                is_admin_user = settings.is_admin(tg_user.id, tg_user.username)

                if db_user is None:
                    db_user = User(
                        telegram_id=tg_user.id,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name,
                        is_admin=is_admin_user,
                        is_blocked=False,
                    )
                    session.add(db_user)
                    await session.flush()
                else:
                    # Ma'lumotlarni yangilaymiz
                    db_user.username = tg_user.username
                    db_user.first_name = tg_user.first_name
                    db_user.last_name = tg_user.last_name
                    db_user.last_active_at = utc_now()
                    if is_admin_user and not db_user.is_admin:
                        db_user.is_admin = True
                    if db_user.is_blocked:
                        db_user.is_blocked = False

                data["db_user"] = db_user
                user = db_user

        return await handler(event, data)
