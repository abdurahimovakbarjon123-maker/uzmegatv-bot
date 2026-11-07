import urllib.parse
from typing import List, Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.models import Movie, MovieFile, RequiredChannel


def get_start_inline_keyboard() -> InlineKeyboardMarkup:
    """Asosiy start menyusi inline tugmalari."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔎 Kino qidirish", callback_data="menu_search"),
            InlineKeyboardButton(text="🎬 Kinolar katalogi", callback_data="catalog:1"),
        ],
        [
            InlineKeyboardButton(text="🔥 TOP kinolar", callback_data="top_movies:1"),
            InlineKeyboardButton(text="🆕 Yangi kinolar", callback_data="new_movies:1"),
        ],
        [
            InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="favorites:1"),
            InlineKeyboardButton(text="🎲 Tasodifiy kino", callback_data="random_movie"),
        ],
        [
            InlineKeyboardButton(text="📞 Yordam", callback_data="menu_help"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_movie_inline_keyboard(
    movie: Movie,
    is_fav: bool = False,
    current_part: int = 1,
    files: Optional[List[MovieFile]] = None,
    bot_username: Optional[str] = "uz_megatv_bot",
) -> InlineKeyboardMarkup:
    """Kino bilan birga yuboriladigan harakatlar klaviaturasi."""
    buttons: List[List[InlineKeyboardButton]] = []

    # 1. Agar bir nechta qismlar bo'lsa, qismlar tugmalari
    if files and len(files) > 1:
        part_row: List[InlineKeyboardButton] = []
        for f in files:
            label = f"{'▶️ ' if f.part_number == current_part else ''}{f.part_name or f'{f.part_number}-qism'}"
            part_row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"movie_part:{movie.code}:{f.part_number}",
                )
            )
            # Har qatorda ko'pi bilan 3 ta qism tugmasi
            if len(part_row) == 3:
                buttons.append(part_row)
                part_row = []
        if part_row:
            buttons.append(part_row)

    # 2. Sevimlilar va Ulashish tugmalari
    fav_text = "💔 Sevimlilardan o‘chirish" if is_fav else "❤️ Sevimlilarga qo‘shish"
    fav_cb = f"fav_del:{movie.id}" if is_fav else f"fav_add:{movie.id}"

    clean_bot = (bot_username or "uz_megatv_bot").lstrip("@")
    share_text = f"🎬 {movie.title} kinoni tomosha qiling!\nKodi: {movie.code}\nBot: https://t.me/{clean_bot}?start=movie_{movie.code}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_text)}"

    buttons.append([
        InlineKeyboardButton(text=fav_text, callback_data=fav_cb),
        InlineKeyboardButton(text="🔗 Ulashish", url=share_url),
    ])

    # 3. Boshqa kinolar va shikoyat
    buttons.append([
        InlineKeyboardButton(text="🎬 Boshqa kinolar", callback_data="catalog:1"),
        InlineKeyboardButton(text="⚠️ Xabar berish", callback_data=f"report_movie:{movie.id}"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscription_keyboard(
    channels: List[RequiredChannel], target_code: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Majburiy kanallarga obuna bo'lish tugmalari va tekshirish tugmasi."""
    buttons: List[List[InlineKeyboardButton]] = []

    for idx, ch in enumerate(channels, 1):
        url = ch.invite_link
        if not url and ch.username:
            url = f"https://t.me/{ch.username.lstrip('@')}"
        if not url:
            url = "https://t.me"

        buttons.append([
            InlineKeyboardButton(text=f"📢 {idx}-kanalga obuna bo‘lish", url=url)
        ])

    check_data = f"check_sub:{target_code}" if target_code else "check_sub:none"
    buttons.append([
        InlineKeyboardButton(text="✅ Tekshirish", callback_data=check_data)
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Administrator boshqaruv paneli menyusi."""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Kino qo‘shish", callback_data="admin_add_movie"),
            InlineKeyboardButton(text="🗑 Kino o‘chirish", callback_data="admin_delete_movie"),
        ],
        [
            InlineKeyboardButton(text="✏️ Kino tahrirlash", callback_data="admin_edit_movie"),
            InlineKeyboardButton(text="📋 Kinolar ro‘yxati", callback_data="admin_movie_list:1"),
        ],
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users_info"),
            InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings"),
        ],
        [
            InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_settings_keyboard(sub_enabled: bool) -> InlineKeyboardMarkup:
    """Admin sozlamalari klaviaturasi."""
    sub_status_text = "🟢 Yoqilgan (O'chirish)" if sub_enabled else "🔴 O'chirilgan (Yoqish)"
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"Majburiy obuna: {sub_status_text}",
                callback_data="admin_toggle_sub",
            )
        ],
        [
            InlineKeyboardButton(text="📢 Kanallar ro'yxati", callback_data="admin_channels_list"),
            InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel"),
        ],
        [
            InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_home"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_movies_pagination_keyboard(
    movies: List[Movie],
    current_page: int,
    total_pages: int,
    prefix: str = "catalog",
) -> InlineKeyboardMarkup:
    """Kinolar ro'yxati va sahifalash (pagination) klaviaturasi."""
    buttons: List[List[InlineKeyboardButton]] = []

    # Kinolar tugmalari
    for m in movies:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 [{m.code}] {m.title} ({m.year})",
                callback_data=f"show_movie:{m.code}",
            )
        ])

    # Navigatsiya tugmalari
    nav_row: List[InlineKeyboardButton] = []
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:{current_page - 1}")
        )
    nav_row.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{max(1, total_pages)}", callback_data="noop")
    )
    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:{current_page + 1}")
        )

    buttons.append(nav_row)
    buttons.append([
        InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_menu_keyboard() -> InlineKeyboardMarkup:
    """Kino qidiruv menyusi inline tugmalari."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔎 Nomi bo‘yicha qidirish", callback_data="search_by_name"),
        ],
        [
            InlineKeyboardButton(text="🎭 Janrlar bo‘yicha", callback_data="search_genres_list"),
            InlineKeyboardButton(text="📅 Chiqqan yili bo‘yicha", callback_data="search_by_year"),
        ],
        [
            InlineKeyboardButton(text="🎲 Tasodifiy kino", callback_data="random_movie"),
            InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(confirm_cb: str, cancel_cb: str = "cancel_action") -> InlineKeyboardMarkup:
    """Tasdiqlash klaviaturasi (Saqlash / Bekor qilish)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Saqlash", callback_data=confirm_cb),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_cb),
            ]
        ]
    )
