import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Foydalanuvchilarning spam yuborishini oldini oluvchi
    va Telegram API Flood cheklovlariga tushib qolmaslikni ta'minlovchi middleware.
    """

    def __init__(self, rate_limit: float = settings.THROTTLE_RATE) -> None:
        super().__init__()
        self.rate_limit = rate_limit
        self.user_last_action: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last_time = self.user_last_action.get(user_id, 0.0)

            # Agar belgilangan vaqtdan tezroq so'rov yuborilsa
            if now - last_time < self.rate_limit:
                if isinstance(event, Message):
                    await event.answer("⚠️ Iltimos, juda tez so'rov yubormang! Bir oz kuting.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Iltimos, biroz kuting...", show_alert=False)
                return None

            self.user_last_action[user_id] = now

        return await handler(event, data)
