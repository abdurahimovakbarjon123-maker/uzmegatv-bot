import logging
from typing import List, Optional, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BotSetting, RequiredChannel

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Majburiy kanallarga a'zolikni boshqarish va tekshirish xizmati."""

    @staticmethod
    async def is_subscription_required(session: AsyncSession) -> bool:
        """Majburiy obuna yoqilganligini tekshirish."""
        setting = await session.scalar(
            select(BotSetting).where(BotSetting.key == "subscription_required")
        )
        if not setting:
            return False
        return setting.value.strip().lower() in ("true", "1", "yes")

    @staticmethod
    async def set_subscription_required(session: AsyncSession, enabled: bool) -> None:
        """Majburiy obuna holatini o'zgartirish."""
        setting = await session.scalar(
            select(BotSetting).where(BotSetting.key == "subscription_required")
        )
        val = "true" if enabled else "false"
        if setting:
            setting.value = val
        else:
            session.add(
                BotSetting(
                    key="subscription_required",
                    value=val,
                    description="Majburiy obuna faolligi (true/false)",
                )
            )
        await session.flush()

    @staticmethod
    async def get_active_channels(session: AsyncSession) -> List[RequiredChannel]:
        """Faol majburiy kanallar ro'yxatini olish."""
        stmt = select(RequiredChannel).where(RequiredChannel.is_active.is_(True))
        return list(await session.scalars(stmt))

    @staticmethod
    async def add_channel(
        session: AsyncSession,
        channel_id: int,
        title: str,
        username: Optional[str] = None,
        invite_link: Optional[str] = None,
    ) -> RequiredChannel:
        """Yangi kanal qo'shish."""
        existing = await session.scalar(
            select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
        )
        if existing:
            existing.title = title
            existing.username = username
            existing.invite_link = invite_link
            existing.is_active = True
            await session.flush()
            return existing

        new_ch = RequiredChannel(
            channel_id=channel_id,
            title=title,
            username=username,
            invite_link=invite_link,
            is_active=True,
        )
        session.add(new_ch)
        await session.flush()
        return new_ch

    @staticmethod
    async def remove_channel(session: AsyncSession, channel_id: int) -> bool:
        """Kanalni o'chirish."""
        ch = await session.scalar(
            select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
        )
        if ch:
            await session.delete(ch)
            await session.flush()
            return True
        return False

    @staticmethod
    async def check_user_subscription(
        bot: Bot, session: AsyncSession, user_id: int
    ) -> Tuple[bool, List[RequiredChannel]]:
        """
        Foydalanuvchi barcha talab qilingan kanallarga a'zo ekanligini tekshiradi.
        Qaytadi: (is_subscribed: bool, unjoined_channels: list)
        """
        # 1. Majburiy obuna yoqilganmi?
        if not await SubscriptionService.is_subscription_required(session):
            return True, []

        channels = await SubscriptionService.get_active_channels(session)
        if not channels:
            return True, []

        unjoined: List[RequiredChannel] = []

        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch.channel_id, user_id=user_id)
                # Telegram a'zolik statuslari: 'creator', 'administrator', 'member', 'restricted'
                if member.status in ("left", "kicked"):
                    unjoined.append(ch)
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa, log qilib o'tkazib yuboramiz
                logger.warning(
                    f"Kanalga a'zolikni tekshirib bo'lmadi (ID: {ch.channel_id}): {e}"
                )
            except Exception as e:
                logger.error(f"Kutilmagan xatolik obunani tekshirishda: {e}")

        is_sub = len(unjoined) == 0
        return is_sub, unjoined
