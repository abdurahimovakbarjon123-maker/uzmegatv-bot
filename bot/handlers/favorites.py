import math
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.keyboards.inline import (
    get_movie_inline_keyboard,
    get_movies_pagination_keyboard,
    get_start_inline_keyboard,
)
from bot.services.movie_service import MovieService

router = Router(name="favorites_router")


@router.callback_query(F.data.startswith("fav_add:"))
async def handle_add_favorite(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Kinoni foydalanuvchining sevimlilariga qo'shish."""
    movie_id_str = callback.data.split(":")[1]
    if not movie_id_str.isdigit():
        return
    movie_id = int(movie_id_str)

    if not db_user:
        await callback.answer("Foydalanuvchi ma'lumotlari topilmadi!", show_alert=True)
        return

    added = await MovieService.add_favorite(session, db_user.id, movie_id)
    if added:
        await callback.answer("❤️ Sevimlilarga qo‘shildi!", show_alert=False)
    else:
        await callback.answer("Bu kino allaqachon sevimlilaringizda bor!", show_alert=False)

    # Tugmani yangilaymiz
    movie = await MovieService.get_by_id(session, movie_id)
    if movie and callback.message:
        bot_info = await callback.bot.get_me()
        markup = get_movie_inline_keyboard(
            movie=movie,
            is_fav=True,
            current_part=1,
            files=movie.files,
            bot_username=bot_info.username or settings.BOT_USERNAME or "uz_megatv_bot",
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except Exception:
            pass


@router.callback_query(F.data.startswith("fav_del:"))
async def handle_delete_favorite(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Kinoni sevimlilardan o'chirish."""
    movie_id_str = callback.data.split(":")[1]
    if not movie_id_str.isdigit():
        return
    movie_id = int(movie_id_str)

    if not db_user:
        await callback.answer("Foydalanuvchi ma'lumotlari topilmadi!", show_alert=True)
        return

    removed = await MovieService.remove_favorite(session, db_user.id, movie_id)
    if removed:
        await callback.answer("💔 Sevimlilardan olib tashlandi!", show_alert=False)
    else:
        await callback.answer("Bu kino sevimlilaringizda topilmadi!", show_alert=False)

    # Tugmani yangilaymiz
    movie = await MovieService.get_by_id(session, movie_id)
    if movie and callback.message:
        bot_info = await callback.bot.get_me()
        markup = get_movie_inline_keyboard(
            movie=movie,
            is_fav=False,
            current_part=1,
            files=movie.files,
            bot_username=bot_info.username or settings.BOT_USERNAME or "uz_megatv_bot",
        )
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except Exception:
            pass


@router.callback_query(F.data.startswith("favorites:"))
async def handle_user_favorites_list(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Foydalanuvchining barcha sevimli kinolari ro'yxati (sahifalash bilan)."""
    if not db_user:
        await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return

    page_str = callback.data.split(":")[1]
    page = int(page_str) if page_str.isdigit() else 1
    page_size = settings.ITEMS_PER_PAGE

    movies, total = await MovieService.get_user_favorites(
        session=session, user_id=db_user.id, page=page, page_size=page_size
    )

    if not movies:
        text = (
            "❤️ <b>SEVIMLI KINOLAR RO‘YXATI BO‘SH!</b>\n\n"
            "Siz hali birorta ham kinoni sevimlilarga saqlamagansiz.\n"
            "Kinoni tomosha qilayotganda <b>'❤️ Sevimlilarga qo‘shish'</b> tugmasini bosing."
        )
        if callback.message:
            await callback.message.edit_text(
                text=text, reply_markup=get_start_inline_keyboard()
            )
        await callback.answer()
        return

    total_pages = math.ceil(total / page_size)
    text = (
        "❤️ <b>SIZNING SEVIMLI KINOLARINGIZ:</b>\n\n"
        f"Jami saqlangan kinolar: <b>{total}</b> ta\n"
        "Tomosha qilish uchun kinoni tanlang:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=page, total_pages=total_pages, prefix="favorites"
    )

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()
