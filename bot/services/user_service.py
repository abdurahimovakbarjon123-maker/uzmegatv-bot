from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User


class UserService:
    """Foydalanuvchilar bilan ishlash xizmati."""

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await session.scalar(stmt)

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return await session.scalar(stmt)

    @staticmethod
    async def set_blocked(session: AsyncSession, telegram_id: int, is_blocked: bool = True) -> None:
        user = await UserService.get_by_telegram_id(session, telegram_id)
        if user:
            user.is_blocked = is_blocked
            await session.flush()
