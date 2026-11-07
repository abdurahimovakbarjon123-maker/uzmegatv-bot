from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BotSetting, Movie


async def get_next_movie_code(session: AsyncSession) -> int:
    """
    Keyingi takrorlanmas kino kodini avtomatik hisoblaydi va kafolatlaydi.
    Kino o'chirilgan taqdirda ham eski kodlar qayta ishlatilmaydi.
    """
    # 1. Bazadagi mavjud maksimal kodni olamiz
    max_code_in_movies = await session.scalar(select(func.max(Movie.code)))
    max_code_in_movies = max_code_in_movies or 0

    # 2. Sozlamalardagi eng yuqori berilgan kodni tekshiramiz
    setting = await session.scalar(
        select(BotSetting).where(BotSetting.key == "highest_movie_code")
    )

    if setting is None:
        highest_recorded = max_code_in_movies
        setting = BotSetting(
            key="highest_movie_code",
            value=str(highest_recorded),
            description="Tizim tomonidan berilgan eng yuqori kino kodi",
        )
        session.add(setting)
        await session.flush()
    else:
        highest_recorded = int(setting.value) if setting.value.isdigit() else max_code_in_movies

    # Yangi kod doimo avvalgi eng kattasidan kamida 1 ga katta bo'ladi
    next_code = max(max_code_in_movies, highest_recorded) + 1

    # Saqlab qo'yamiz
    setting.value = str(next_code)
    await session.flush()

    return next_code


async def is_code_available(session: AsyncSession, code: int) -> bool:
    """Berilgan kod bazada bo'sh ekanligini tekshiradi."""
    existing = await session.scalar(select(Movie).where(Movie.code == code))
    return existing is None


async def sync_highest_code(session: AsyncSession, manual_code: int) -> None:
    """Agar admin qo'lda kattaroq kod kiritgan bo'lsa, hisoblagichni moslashtiramiz."""
    setting = await session.scalar(
        select(BotSetting).where(BotSetting.key == "highest_movie_code")
    )
    if setting:
        current_highest = int(setting.value) if setting.value.isdigit() else 0
        if manual_code > current_highest:
            setting.value = str(manual_code)
            await session.flush()
    else:
        setting = BotSetting(
            key="highest_movie_code",
            value=str(manual_code),
            description="Tizim tomonidan berilgan eng yuqori kino kodi",
        )
        session.add(setting)
        await session.flush()
