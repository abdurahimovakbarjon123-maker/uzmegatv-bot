import html
from typing import Optional

from bot.database.models import Movie


def format_movie_caption(
    movie: Movie,
    part_info: Optional[str] = None,
    bot_username: Optional[str] = "uz_megatv_bot",
) -> str:
    """
    Kino uchun standart va chiroyli ma'lumot matnini shakllantiradi.
    Telegram caption cheklovi (1024 belgi) hisobga olingan.
    """
    title = html.escape(movie.title or "Noma'lum")
    genre = html.escape(movie.genre or "Noma'lum")
    language = html.escape(movie.language or "O‘zbekcha")
    rating = movie.rating if movie.rating is not None else 0.0
    rating_str = f"{rating:.1f}/10" if rating > 0 else "Aniqlanmagan"

    part_text = f"\n📦 Qism: {html.escape(part_info)}" if part_info else ""

    header = (
        f"🎬 <b>Kino:</b> {title}\n"
        f"🔢 <b>Kodi:</b> <code>{movie.code}</code>\n"
        f"🎭 <b>Janr:</b> {genre}\n"
        f"📅 <b>Yili:</b> {movie.year}\n"
        f"🌍 <b>Tili:</b> {language}\n"
        f"⭐ <b>Reyting:</b> {rating_str}"
        f"{part_text}\n"
    )

    clean_bot = (bot_username or "uz_megatv_bot").lstrip("@")
    footer = f"\n\n📺 <b>UZMEGATV — Eng sara kinolar olami!</b>\n🤖 @{clean_bot}"

    # Description length management
    available_len = 1000 - len(header) - len(footer)
    desc = movie.description or "Tavsif mavjud emas."
    desc = html.escape(desc)

    if len(desc) > available_len:
        desc = desc[: max(available_len - 15, 50)] + "..."

    return f"{header}\n📝 <b>Tavsif:</b> {desc}{footer}"


def format_file_size(size_in_bytes: Optional[int]) -> str:
    """Baytlarni MB yoki GB formatiga o'tkazadi."""
    if not size_in_bytes:
        return "Noma'lum"
    mb = size_in_bytes / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.1f} MB"


def extract_movie_code_from_deeplink(payload: str) -> Optional[int]:
    """
    /start buyrug'idagi deep-link parametrlaridan kino kodini ajratib oladi.
    Masalan: 'movie_125' yoki '125' yoki 'code_125' -> 125
    """
    if not payload:
        return None
    cleaned = payload.strip().lower()
    if cleaned.startswith("movie_"):
        cleaned = cleaned[6:]
    elif cleaned.startswith("code_"):
        cleaned = cleaned[5:]

    if cleaned.isdigit():
        return int(cleaned)
    return None
