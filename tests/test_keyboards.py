from bot.database.models import Movie, MovieFile, RequiredChannel
from bot.keyboards.inline import (
    get_admin_main_keyboard,
    get_admin_settings_keyboard,
    get_movie_inline_keyboard,
    get_movies_pagination_keyboard,
    get_search_menu_keyboard,
    get_start_inline_keyboard,
    get_subscription_keyboard,
)


def test_start_inline_keyboard():
    """Start menyusi tugmalarini tekshirish."""
    markup = get_start_inline_keyboard()
    button_texts = [btn.text for row in markup.inline_keyboard for btn in row]

    assert "🔎 Kino qidirish" in button_texts
    assert "🎬 Kinolar katalogi" in button_texts
    assert "🔥 TOP kinolar" in button_texts
    assert "🆕 Yangi kinolar" in button_texts
    assert "❤️ Sevimlilar" in button_texts
    assert "📞 Yordam" in button_texts


def test_movie_inline_keyboard_favorite_toggle():
    """Kino klaviaturasida sevimlilar holatini tekshirish."""
    movie = Movie(id=1, code=125, title="Interstellar", year=2014)

    # Sevimli emas bo'lganda
    markup_not_fav = get_movie_inline_keyboard(movie, is_fav=False)
    texts_not_fav = [btn.text for row in markup_not_fav.inline_keyboard for btn in row]
    assert "❤️ Sevimlilarga qo‘shish" in texts_not_fav

    # Sevimli bo'lganda
    markup_fav = get_movie_inline_keyboard(movie, is_fav=True)
    texts_fav = [btn.text for row in markup_fav.inline_keyboard for btn in row]
    assert "💔 Sevimlilardan o‘chirish" in texts_fav


def test_movie_inline_keyboard_multipart():
    """Ko'p qismli kino uchun qismlar tugmalarini tekshirish."""
    movie = Movie(id=1, code=125, title="Interstellar", year=2014)
    files = [
        MovieFile(part_number=1, part_name="1-qism", file_id="vid1"),
        MovieFile(part_number=2, part_name="2-qism", file_id="vid2"),
    ]

    markup = get_movie_inline_keyboard(movie, is_fav=False, current_part=1, files=files)
    btn_callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]

    assert "movie_part:125:1" in btn_callbacks
    assert "movie_part:125:2" in btn_callbacks


def test_subscription_keyboard():
    """Majburiy kanal tugmalari va tekshirish tugmasi."""
    channels = [
        RequiredChannel(channel_id=-1001, title="Kanal 1", username="kanal1", invite_link="https://t.me/kanal1"),
        RequiredChannel(channel_id=-1002, title="Kanal 2", username="kanal2", invite_link="https://t.me/kanal2"),
    ]
    markup = get_subscription_keyboard(channels, target_code=125)
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row if btn.callback_data]

    assert "📢 1-kanalga obuna bo‘lish" in texts
    assert "📢 2-kanalga obuna bo‘lish" in texts
    assert "✅ Tekshirish" in texts
    assert "check_sub:125" in callbacks


def test_admin_main_keyboard():
    """Admin boshqaruv paneli tugmalari."""
    markup = get_admin_main_keyboard()
    texts = [btn.text for row in markup.inline_keyboard for btn in row]

    assert "➕ Kino qo‘shish" in texts
    assert "🗑 Kino o‘chirish" in texts
    assert "✏️ Kino tahrirlash" in texts
    assert "📋 Kinolar ro‘yxati" in texts
    assert "📊 Statistika" in texts
    assert "📢 Xabar yuborish" in texts
    assert "👥 Foydalanuvchilar" in texts
    assert "⚙️ Sozlamalar" in texts


def test_admin_settings_keyboard():
    """Admin sozlamalar tugmalari."""
    markup_on = get_admin_settings_keyboard(sub_enabled=True)
    texts_on = [btn.text for row in markup_on.inline_keyboard for btn in row]
    assert any("🟢 Yoqilgan" in t for t in texts_on)

    markup_off = get_admin_settings_keyboard(sub_enabled=False)
    texts_off = [btn.text for row in markup_off.inline_keyboard for btn in row]
    assert any("🔴 O'chirilgan" in t for t in texts_off)
