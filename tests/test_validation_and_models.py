import pytest
from bot.database.models import (
    Admin,
    BotSetting,
    Broadcast,
    Favorite,
    Movie,
    MovieFile,
    MovieRequest,
    RequiredChannel,
    User,
)
from bot.utils.helpers import extract_movie_code_from_deeplink, format_file_size, format_movie_caption


def test_movie_model_structure():
    """Kino modelining barcha maydonlari va xususiyatlarini tekshirish."""
    movie = Movie(
        code=125,
        title="Interstellar",
        original_title="Interstellar",
        genre="Fantastika",
        year=2014,
        language="O‘zbekcha",
        rating=8.7,
        description="Ajoyib kosmik sayohat haqida film",
        poster_file_id="AgACAgIAAxkBAAIF...",
        is_active=True,
        views_count=50,
    )
    assert movie.code == 125
    assert movie.title == "Interstellar"
    assert movie.year == 2014
    assert movie.rating == 8.7
    assert movie.is_active is True
    assert movie.views_count == 50


def test_multipart_movie_files():
    """Ko'p qismli kino fayllarining modeli va tartiblanishi."""
    movie = Movie(id=1, code=500, title="Garri Potter", genre="Fantastika", year=2001)
    file1 = MovieFile(id=1, movie_id=1, file_id="vid_part1", part_number=1, part_name="1-qism")
    file2 = MovieFile(id=2, movie_id=1, file_id="vid_part2", part_number=2, part_name="2-qism")
    movie.files = [file1, file2]

    assert len(movie.files) == 2
    assert movie.files[0].part_number == 1
    assert movie.files[1].part_number == 2
    assert movie.files[0].part_name == "1-qism"
    assert movie.files[1].part_name == "2-qism"


def test_missing_video_file_handling():
    """Kino bazada bor, lekin Telegram video file_id si yo'q holatini tekshirish."""
    movie = Movie(
        id=10,
        code=999,
        title="Faylsiz kino",
        genre="Drama",
        year=2024,
        poster_file_id=None,
    )
    movie.files = []
    caption = format_movie_caption(movie)

    assert "Faylsiz kino" in caption
    assert "<code>999</code>" in caption
    assert len(movie.files) == 0


def test_required_channel_model():
    """Majburiy kanal modeli tekshiruvi."""
    ch = RequiredChannel(
        channel_id=-1001234567890,
        title="UZMEGATV Rasmiy",
        username="uzmegatv_rasmiy",
        invite_link="https://t.me/uzmegatv_rasmiy",
        is_active=True,
    )
    assert ch.channel_id == -1001234567890
    assert ch.title == "UZMEGATV Rasmiy"
    assert ch.is_active is True


def test_user_and_favorite_relationship():
    """Foydalanuvchi va sevimli kinolar bog'liqligi."""
    user = User(id=1, telegram_id=987654321, username="kinochi_uz", is_admin=False)
    movie = Movie(id=1, code=125, title="Interstellar")
    fav = Favorite(id=1, user_id=1, movie_id=1, user=user, movie=movie)

    assert fav.user_id == 1
    assert fav.movie_id == 1
    assert fav.movie.title == "Interstellar"
    assert fav.user.username == "kinochi_uz"


def test_bot_settings_model():
    """Bot sozlamalari modeli tekshiruvi."""
    setting = BotSetting(
        key="subscription_required",
        value="true",
        description="Majburiy obuna holati",
    )
    assert setting.key == "subscription_required"
    assert setting.value == "true"


def test_broadcast_model():
    """Xabar tarqatish modeli tekshiruvi."""
    bc = Broadcast(
        admin_id=123456789,
        message_type="photo",
        content="Yangi kino yuklandi!",
        file_id="AgACAgIAAxk...",
        total_users=5000,
        sent_count=4850,
        failed_count=150,
        status="completed",
    )
    assert bc.admin_id == 123456789
    assert bc.sent_count == 4850
    assert bc.failed_count == 150
    assert bc.status == "completed"
