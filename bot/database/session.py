import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings
from bot.database.base import Base
from bot.database.models import BotSetting

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables and default configuration."""
    logger.info("Ma'lumotlar bazasini initsializatsiya qilish boshlandi...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Jadvallar muvaffaqiyatli tekshirildi/yaratildi.")

    # Standart sozlamalarni tekshirish va kiritish
    async with async_session() as session:
        default_settings = [
            ("subscription_required", "false", "Majburiy obuna faolligi (true/false)"),
            ("welcome_text", "🎬 UZMEGATV — Kino olamiga xush kelibsiz!", "Boshlang'ich tabrik matni"),
            ("support_contact", "@abdurahimoovvvv", "Aloqa va yordam uchun admin username"),
        ]
        for key, val, desc in default_settings:
            existing = await session.scalar(
                select(BotSetting).where(BotSetting.key == key)
            )
            if not existing:
                session.add(BotSetting(key=key, value=val, description=desc))
        await session.commit()
    logger.info("Standart sozlamalar o'rnatildi.")


async def close_db() -> None:
    """Gracefully close database engine connections."""
    logger.info("Ma'lumotlar bazasi ulanishlari yopilmoqda...")
    await engine.dispose()
    logger.info("Ma'lumotlar bazasi muvaffaqiyatli yopildi.")
