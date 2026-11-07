import asyncio
import logging
import time
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.database.base import utc_now
from bot.database.models import Broadcast, User

logger = logging.getLogger(__name__)


class BroadcastService:
    """Xabarlarni barcha faol foydalanuvchilarga xavfsiz va tezkor tarqatish xizmati."""

    @staticmethod
    async def run_broadcast_task(
        bot: Bot,
        session_pool: async_sessionmaker,
        admin_id: int,
        broadcast_id: int,
        message_type: str,
        text: Optional[str] = None,
        photo_id: Optional[str] = None,
        video_id: Optional[str] = None,
    ) -> None:
        """Orqa fonda (background async task) xabar yuborish."""
        start_time = time.time()
        sent_count = 0
        failed_count = 0

        # Foydalanuvchilar ro'yxatini olamiz
        async with session_pool() as session:
            stmt = select(User.telegram_id).where(User.is_blocked.is_(False))
            user_ids = list(await session.scalars(stmt))
            total_users = len(user_ids)

            # Broadcast statusini 'running' qilamiz
            bc = await session.get(Broadcast, broadcast_id)
            if bc:
                bc.total_users = total_users
                bc.status = "running"
                await session.commit()

        logger.info(f"Tarqatish boshlandi: {total_users} ta foydalanuvchiga.")

        for uid in user_ids:
            try:
                if message_type == "text" and text:
                    await bot.send_message(chat_id=uid, text=text)
                elif message_type == "photo" and photo_id:
                    await bot.send_photo(chat_id=uid, photo=photo_id, caption=text)
                elif message_type == "video" and video_id:
                    await bot.send_video(chat_id=uid, video=video_id, caption=text)

                sent_count += 1
            except TelegramRetryAfter as e:
                logger.warning(f"Flood limit: {e.retry_after} soniya kutilmoqda...")
                await asyncio.sleep(e.retry_after)
                # Qayta urinish
                try:
                    if message_type == "text" and text:
                        await bot.send_message(chat_id=uid, text=text)
                    elif message_type == "photo" and photo_id:
                        await bot.send_photo(chat_id=uid, photo=photo_id, caption=text)
                    elif message_type == "video" and video_id:
                        await bot.send_video(chat_id=uid, video=video_id, caption=text)
                    sent_count += 1
                except Exception:
                    failed_count += 1
            except TelegramForbiddenError:
                # Foydalanuvchi botni bloklagan
                failed_count += 1
                async with session_pool() as session:
                    user_stmt = select(User).where(User.telegram_id == uid)
                    db_u = await session.scalar(user_stmt)
                    if db_u:
                        db_u.is_blocked = True
                        await session.commit()
            except Exception as e:
                failed_count += 1
                logger.debug(f"Xabar yetkazilmadi (ID: {uid}): {e}")

            # Telegram flood limit: ~25 ta xabar/sekund
            await asyncio.sleep(0.04)

        elapsed = round(time.time() - start_time, 1)

        # Natijalarni bazaga yozish
        async with session_pool() as session:
            bc = await session.get(Broadcast, broadcast_id)
            if bc:
                bc.sent_count = sent_count
                bc.failed_count = failed_count
                bc.status = "completed"
                bc.finished_at = utc_now()
                await session.commit()

        # Adminga hisobot yuborish
        report = (
            "📢 <b>Xabar tarqatish yakunlandi!</b>\n\n"
            f"👥 Jami qamrov: <b>{total_users:,}</b> ta\n"
            f"✅ Muvaffaqiyatli yetkazildi: <b>{sent_count:,}</b> ta\n"
            f"❌ Xatolik (bloklaganlar): <b>{failed_count:,}</b> ta\n"
            f"⏱ Sarflangan vaqt: <b>{elapsed}</b> sekund"
        )
        try:
            await bot.send_message(chat_id=admin_id, text=report)
        except Exception as e:
            logger.error(f"Adminga hisobot yuborishda xatolik: {e}")
