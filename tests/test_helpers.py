from bot.database.models import Movie
from bot.utils.helpers import (
    extract_movie_code_from_deeplink,
    format_file_size,
    format_movie_caption,
)


def test_extract_movie_code_from_deeplink():
    """Deep-link parametrlaridan kino kodini ajratib olish testi."""
    assert extract_movie_code_from_deeplink("movie_125") == 125
    assert extract_movie_code_from_deeplink("code_1000") == 1000
    assert extract_movie_code_from_deeplink("1") == 1
    assert extract_movie_code_from_deeplink("movie_abc") is None
    assert extract_movie_code_from_deeplink("") is None
    assert extract_movie_code_from_deeplink(None) is None


def test_format_file_size():
    """Fayl hajmini formatlash testi."""
    assert format_file_size(None) == "Noma'lum"
    assert format_file_size(0) == "Noma'lum"
    assert "MB" in format_file_size(500 * 1024 * 1024)
    assert "GB" in format_file_size(2 * 1024 * 1024 * 1024)


def test_format_movie_caption():
    """Kino tavsifi matnini to'liq formatlash testi."""
    movie = Movie(
        code=125,
        title="Interstellar",
        genre="Fantastika",
        year=2014,
        language="O‘zbekcha",
        rating=8.7,
        description="Kosmik sayohat va insoniyat kelajagi haqida ajoyib kino.",
    )
    caption = format_movie_caption(movie)

    assert "🎬 <b>Kino:</b> Interstellar" in caption
    assert "🔢 <b>Kodi:</b> <code>125</code>" in caption
    assert "🎭 <b>Janr:</b> Fantastika" in caption
    assert "📅 <b>Yili:</b> 2014" in caption
    assert "🌍 <b>Tili:</b> O‘zbekcha" in caption
    assert "⭐ <b>Reyting:</b> 8.7/10" in caption
    assert "📺 <b>UZMEGATV" in caption
    assert "@uz_megatv_bot" in caption
    assert len(caption) <= 1024


def test_format_movie_caption_truncation():
    """Juda uzun tavsif 1024 belgidan oshmasligi uchun qisqartirilishi testi."""
    huge_description = "A" * 2000
    movie = Movie(
        code=999,
        title="Uzun Kino",
        genre="Drama",
        year=2023,
        language="O‘zbekcha",
        rating=7.0,
        description=huge_description,
    )
    caption = format_movie_caption(movie)
    assert len(caption) <= 1024
    assert "..." in caption
