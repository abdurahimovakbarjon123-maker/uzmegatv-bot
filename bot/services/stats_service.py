from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Movie, MovieRequest, User


class StatsService:
    """Haqiqiy ma'lumotlar bazasi ko'rsatkichlari bo'yicha statistika xizmati."""

    @staticmethod
    async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # 1. Jami foydalanuvchilar
        total_users = (
            await session.scalar(select(func.count(User.id)))
        ) or 0

        # 2. Bugun qo'shilgan yangi foydalanuvchilar
        new_users_today = (
            await session.scalar(
                select(func.count(User.id)).where(User.created_at >= today_start)
            )
        ) or 0

        # 3. Faol foydalanuvchilar (DAU, WAU, MAU)
        dau = (
            await session.scalar(
                select(func.count(User.id)).where(User.last_active_at >= day_ago)
            )
        ) or 0

        wau = (
            await session.scalar(
                select(func.count(User.id)).where(User.last_active_at >= week_ago)
            )
        ) or 0

        mau = (
            await session.scalar(
                select(func.count(User.id)).where(User.last_active_at >= month_ago)
            )
        ) or 0

        # 4. Jami kinolar soni
        total_movies = (
            await session.scalar(
                select(func.count(Movie.id)).where(Movie.is_active.is_(True))
            )
        ) or 0

        # 5. Jami kino so'rovlari soni
        total_requests = (
            await session.scalar(select(func.count(MovieRequest.id)))
        ) or 0

        # 6. Eng ko'p so'ralgan / ko'rilgan TOP 5 kino
        top_movies_stmt = (
            select(Movie)
            .where(Movie.is_active.is_(True))
            .order_by(desc(Movie.views_count), desc(Movie.id))
            .limit(5)
        )
        top_movies = list(await session.scalars(top_movies_stmt))

        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "total_movies": total_movies,
            "total_requests": total_requests,
            "top_movies": top_movies,
        }

    @staticmethod
    def format_dashboard_text(stats: Dict[str, Any]) -> str:
        """Statistika hisobotini chiroyli o'zbekcha matn holatiga keltiradi."""
        top_movies_str = ""
        if stats["top_movies"]:
            for idx, m in enumerate(stats["top_movies"], 1):
                top_movies_str += f"\n  {idx}. [{m.code}] <b>{m.title}</b> — {m.views_count} marta"
        else:
            top_movies_str = "\n  <i>Hozircha ma'lumot yo'q</i>"

        return (
            "📊 <b>UZMEGATV — TIZIM STATISTIKASI</b>\n\n"
            "👥 <b>Foydalanuvchilar:</b>\n"
            f"• Jami a'zolar: <b>{stats['total_users']:,}</b> ta\n"
            f"• Bugun qo‘shilgan: <b>{stats['new_users_today']:,}</b> ta\n"
            f"• Kunlik faol (DAU 24s): <b>{stats['dau']:,}</b> ta\n"
            f"• Haftalik faol (WAU 7k): <b>{stats['wau']:,}</b> ta\n"
            f"• Oylik faol (MAU 30k): <b>{stats['mau']:,}</b> ta\n\n"
            "🎬 <b>Kino fondi:</b>\n"
            f"• Jami faol kinolar: <b>{stats['total_movies']:,}</b> ta\n"
            f"• Jami kino so‘rovlari: <b>{stats['total_requests']:,}</b> marta\n\n"
            f"🔥 <b>Eng ko‘p ko‘rilgan TOP 5 kino:</b>"
            f"{top_movies_str}\n\n"
            "⏱ <i>Haqiqiy ma'lumotlar bazasi so'rovlari asosida yangilandi.</i>"
        )
