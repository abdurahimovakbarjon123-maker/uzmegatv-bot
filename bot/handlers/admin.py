import asyncio
import math
from typing import Optional
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import Broadcast, Movie, RequiredChannel, User
from bot.database.session import async_session
from bot.keyboards.inline import (
    get_admin_main_keyboard,
    get_admin_settings_keyboard,
    get_confirmation_keyboard,
    get_movies_pagination_keyboard,
    get_start_inline_keyboard,
)
from bot.keyboards.reply import (
    get_cancel_keyboard,
    get_skip_or_cancel_keyboard,
    remove_keyboard,
)
from bot.services.broadcast_service import BroadcastService
from bot.services.movie_service import MovieService
from bot.services.stats_service import StatsService
from bot.services.subscription_service import SubscriptionService
from bot.states.states import (
    AddChannelSG,
    AddMovieSG,
    BroadcastSG,
    DeleteMovieSG,
    EditMovieSG,
)
from bot.utils.code_generator import get_next_movie_code

router = Router(name="admin_router")


def is_admin_check(
    user_id: int, db_user: Optional[User], username: Optional[str] = None
) -> bool:
    """Foydalanuvchi admin ekanligini ID yoki username orqali tekshiradi."""
    u_name = username or (db_user.username if db_user else None)
    if settings.is_admin(user_id, u_name):
        return True
    if db_user and db_user.is_admin:
        return True
    return False


@router.message(Command("cancel"))
@router.message(F.text == "❌ Bekor qilish")
async def handle_cancel_any_workflow(message: Message, state: FSMContext) -> None:
    """Har qanday FSM jarayonini bekor qilish."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Jarayon bekor qilindi.",
            reply_markup=remove_keyboard(),
        )
    else:
        await message.answer(
            "Faol jarayon mavjud emas.",
            reply_markup=remove_keyboard(),
        )


@router.message(Command("admin"))
async def handle_admin_command(
    message: Message, db_user: User
) -> None:
    """Admin boshqaruv panelini ochish."""
    if not is_admin_check(message.from_user.id, db_user):
        await message.answer("⛔️ Kechirasiz, bu buyruq faqat bot administratorlari uchun!")
        return

    admin_text = (
        "👑 <b>UZMEGATV — ADMINISTRATOR PANELI</b>\n\n"
        "Xush kelibsiz! Botni boshqarish uchun quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(
        text=admin_text,
        reply_markup=get_admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin_home")
async def handle_admin_home_callback(
    callback: CallbackQuery, db_user: User
) -> None:
    """Admin bosh menyusiga qaytish."""
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    admin_text = (
        "👑 <b>UZMEGATV — ADMINISTRATOR PANELI</b>\n\n"
        "Boshqaruv menyusidan kerakli bo'limni tanlang:"
    )
    if callback.message:
        await callback.message.edit_text(
            text=admin_text, reply_markup=get_admin_main_keyboard()
        )
    await callback.answer()


# ==============================================================================
# 1. KINO QO'SHISH (ADD MOVIE WORKFLOW - FSM)
# ==============================================================================

@router.callback_query(F.data == "admin_add_movie")
async def handle_add_movie_start(
    callback: CallbackQuery, state: FSMContext, db_user: User
) -> None:
    """Kino qo'shish jarayonini boshlash."""
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.clear()
    await state.set_state(AddMovieSG.waiting_for_title)

    prompt = (
        "➕ <b>YANGI KINO QO‘SHISH</b>\n\n"
        "1-qadam: Kino nomini kiriting:\n"
        "<i>(Masalan: Interstellar yoki Forsaj 10)</i>"
    )
    if callback.message:
        await callback.message.answer(text=prompt, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(AddMovieSG.waiting_for_title)
async def handle_add_movie_title(message: Message, state: FSMContext) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieSG.waiting_for_genre)
    await message.answer(
        "2-qadam: Kino janrini kiriting:\n"
        "<i>(Masalan: Fantastika, Jangari, Komediya)</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_genre)
async def handle_add_movie_genre(message: Message, state: FSMContext) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    await state.update_data(genre=message.text.strip())
    await state.set_state(AddMovieSG.waiting_for_year)
    await message.answer(
        "3-qadam: Chiqqan yilini kiriting:\n"
        "<i>(Masalan: 2024)</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_year)
async def handle_add_movie_year(message: Message, state: FSMContext) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    text = message.text.strip()
    if not text.isdigit() or not (1900 <= int(text) <= 2040):
        await message.answer("⚠️ Iltimos, to'g'ri yil kiriting (masalan: 2024):")
        return

    await state.update_data(year=int(text))
    await state.set_state(AddMovieSG.waiting_for_language)
    await message.answer(
        "4-qadam: Kino tilini kiriting:\n"
        "<i>(Masalan: O‘zbekcha, Ruscha, Subtitr)</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_language)
async def handle_add_movie_language(message: Message, state: FSMContext) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    await state.update_data(language=message.text.strip())
    await state.set_state(AddMovieSG.waiting_for_description)
    await message.answer(
        "5-qadam: Kino haqida qisqacha tavsif (mazmunini) kiriting:\n"
        "<i>(O'tkazib yuborish uchun '➡️ O‘tkazib yuborish' tugmasini bosing)</i>",
        reply_markup=get_skip_or_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_description)
async def handle_add_movie_desc(message: Message, state: FSMContext) -> None:
    desc = None
    if message.text and message.text != "➡️ O‘tkazib yuborish" and message.text != "/skip":
        desc = message.text.strip()
    await state.update_data(description=desc)

    await state.set_state(AddMovieSG.waiting_for_rating)
    await message.answer(
        "6-qadam: Kino reytingini kiriting (0 dan 10 gacha):\n"
        "<i>(Masalan: 8.5 yoki '➡️ O‘tkazib yuborish' bosing)</i>",
        reply_markup=get_skip_or_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_rating)
async def handle_add_movie_rating(message: Message, state: FSMContext) -> None:
    rating = 0.0
    if message.text and message.text not in ("➡️ O‘tkazib yuborish", "/skip"):
        try:
            val = float(message.text.strip().replace(",", "."))
            if 0.0 <= val <= 10.0:
                rating = round(val, 1)
        except ValueError:
            pass
    await state.update_data(rating=rating)

    await state.set_state(AddMovieSG.waiting_for_poster)
    await message.answer(
        "7-qadam: Kino posterini (rasmini) yuboring:\n"
        "<i>(Rasm yuboring yoki o‘tkazib yuborish uchun '➡️ O‘tkazib yuborish' bosing)</i>",
        reply_markup=get_skip_or_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_poster)
async def handle_add_movie_poster(message: Message, state: FSMContext) -> None:
    poster_id = None
    if message.photo:
        poster_id = message.photo[-1].file_id
    elif message.text and message.text in ("➡️ O‘tkazib yuborish", "/skip"):
        poster_id = None
    else:
        await message.answer(
            "⚠️ Iltimos, rasm (poster) yuboring yoki '➡️ O‘tkazib yuborish' tugmasini bosing:"
        )
        return

    await state.update_data(poster_file_id=poster_id)
    await state.set_state(AddMovieSG.waiting_for_video)
    await message.answer(
        "8-qadam: <b>Kino videosini yuboring</b>:\n"
        "<i>(Telegram video yoki hujjat formatida yuboring)</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AddMovieSG.waiting_for_video)
async def handle_add_movie_video(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    video_id = None
    file_type = "video"
    file_size = None
    duration = None

    if message.video:
        video_id = message.video.file_id
        file_type = "video"
        file_size = message.video.file_size
        duration = message.video.duration
    elif message.document:
        video_id = message.document.file_id
        file_type = "document"
        file_size = message.document.file_size
    else:
        await message.answer("⚠️ Iltimos, video yoki video fayl yuboring:")
        return

    # Avtomatik ravishda keyingi kino kodini olamiz
    next_code = await get_next_movie_code(session)
    await state.update_data(
        video_file_id=video_id,
        file_type=file_type,
        file_size=file_size,
        duration=duration,
        movie_code=next_code,
    )

    data = await state.get_data()
    await state.set_state(AddMovieSG.waiting_for_confirmation)

    preview_text = (
        "🎬 <b>YANGI KINO MA‘LUMOTLARI (TASDIQLASH):</b>\n\n"
        f"🔢 Berilgan unikal kod: <code>{next_code}</code>\n"
        f"🎬 Nomi: <b>{data.get('title')}</b>\n"
        f"🎭 Janri: <b>{data.get('genre')}</b>\n"
        f"📅 Yili: <b>{data.get('year')}</b>\n"
        f"🌍 Tili: <b>{data.get('language')}</b>\n"
        f"⭐ Reyting: <b>{data.get('rating')}/10</b>\n"
        f"📝 Tavsif: <i>{data.get('description') or 'Yo‘q'}</i>\n\n"
        "Hammasi to'g'rimi? Kinoni bazaga saqlash uchun 'Saqlash' tugmasini bosing:"
    )

    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Saqlash", callback_data="confirm_save_movie"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action"),
            ]
        ]
    )

    await message.answer("Tekshirib oling:", reply_markup=remove_keyboard())
    if data.get("poster_file_id"):
        try:
            await message.answer_photo(
                photo=data["poster_file_id"],
                caption=preview_text,
                reply_markup=confirm_kb,
            )
            return
        except Exception:
            pass

    await message.answer(text=preview_text, reply_markup=confirm_kb)


@router.callback_query(AddMovieSG.waiting_for_confirmation, F.data == "confirm_save_movie")
async def handle_confirm_save_movie(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Kinoni bazaga muvaffaqiyatli saqlash."""
    data = await state.get_data()
    await state.clear()

    try:
        movie = await MovieService.create_movie(
            session=session,
            title=data["title"],
            genre=data["genre"],
            year=data["year"],
            language=data["language"],
            description=data.get("description"),
            rating=data.get("rating", 0.0),
            video_file_id=data["video_file_id"],
            poster_file_id=data.get("poster_file_id"),
            custom_code=data.get("movie_code"),
            duration=data.get("duration"),
            file_size=data.get("file_size"),
            file_type=data.get("file_type", "video"),
        )
        success_text = (
            f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 Nomi: <b>{movie.title}</b>\n"
            f"🔢 Kodi: <code>{movie.code}</code>\n\n"
            f"Endi foydalanuvchilar botga <code>{movie.code}</code> raqamini yuborib kinoni olishlari mumkin!"
        )
        if callback.message:
            await callback.message.answer(
                text=success_text, reply_markup=get_admin_main_keyboard()
            )
        await callback.answer("Saqlandi!", show_alert=False)
    except Exception as e:
        if callback.message:
            await callback.message.answer(
                f"❌ Saqlashda xatolik yuz berdi: {e}",
                reply_markup=get_admin_main_keyboard(),
            )
        await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def handle_cancel_action_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Amalni bekor qilish callbacki."""
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            "❌ Jarayon bekor qilindi.",
            reply_markup=get_admin_main_keyboard(),
        )
    await callback.answer()


# ==============================================================================
# 2. KINO O'CHIRISH (DELETE MOVIE)
# ==============================================================================

@router.callback_query(F.data == "admin_delete_movie")
async def handle_delete_movie_start(
    callback: CallbackQuery, state: FSMContext, db_user: User
) -> None:
    """Kino o'chirish jarayonini boshlash."""
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(DeleteMovieSG.waiting_for_code)
    text = (
        "🗑 <b>KINO O‘CHIRISH</b>\n\n"
        "O‘chirmoqchi bo‘lgan kinoning kodini yuboring:\n"
        "<i>(Masalan: 125)</i>"
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(DeleteMovieSG.waiting_for_code)
async def handle_delete_movie_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, raqamli kino kodini kiriting:")
        return

    code = int(text)
    movie = await MovieService.get_by_code(session, code)
    if not movie:
        await message.answer(f"❌ #{code} raqamli kino topilmadi.")
        return

    await state.update_data(delete_movie_id=movie.id)
    await state.set_state(DeleteMovieSG.confirm_delete)

    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Ha, o‘chirilsin", callback_data="confirm_delete_now"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action"),
            ]
        ]
    )

    await message.answer(
        f"⚠️ Haqiqatan ham <b>#{movie.code} — {movie.title}</b> kinosini butunlay o‘chirmoqchimisiz?",
        reply_markup=confirm_kb,
    )


@router.callback_query(DeleteMovieSG.confirm_delete, F.data == "confirm_delete_now")
async def handle_confirm_delete(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    movie_id = data.get("delete_movie_id")
    await state.clear()

    if movie_id:
        deleted = await MovieService.delete_movie(session, movie_id)
        if deleted:
            await callback.answer("Kino o'chirildi!", show_alert=True)
            if callback.message:
                await callback.message.edit_text(
                    "✅ Kino bazadan muvaffaqiyatli o‘chirildi.",
                    reply_markup=get_admin_main_keyboard(),
                )
            return

    await callback.answer("O'chirishda xatolik yuz berdi!", show_alert=True)


# ==============================================================================
# 3. KINOLAR RO'YXATI (ADMIN MOVIE LIST)
# ==============================================================================

@router.callback_query(F.data.startswith("admin_movie_list:"))
async def handle_admin_movie_list(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    page_str = callback.data.split(":")[1]
    page = int(page_str) if page_str.isdigit() else 1
    page_size = 8

    movies, total = await MovieService.get_movies_paginated(
        session, page=page, page_size=page_size, order_by="newest"
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    text = (
        "📋 <b>ADMIN — BARCHA KINOLAR RO‘YXATI</b>\n\n"
        f"Jami kinolar soni: <b>{total}</b> ta\n"
        "Ko‘rish uchun tanlang:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=page, total_pages=total_pages, prefix="admin_movie_list"
    )
    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


# ==============================================================================
# 4. STATISTIKA (ADMIN STATS)
# ==============================================================================

@router.callback_query(F.data == "admin_stats")
async def handle_admin_stats(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    stats = await StatsService.get_dashboard_stats(session)
    report_text = StatsService.format_dashboard_text(stats)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_home")],
        ]
    )

    if callback.message:
        await callback.message.edit_text(text=report_text, reply_markup=kb)
    await callback.answer()


# ==============================================================================
# 5. XABAR YUBORISH (BROADCAST SYSTEM)
# ==============================================================================

@router.callback_query(F.data == "admin_broadcast")
async def handle_admin_broadcast_start(
    callback: CallbackQuery, state: FSMContext, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.clear()
    await state.set_state(BroadcastSG.waiting_for_message)

    text = (
        "📢 <b>XABAR YUBORISH (BROADCAST)</b>\n\n"
        "Barcha faol foydalanuvchilarga yubormoqchi bo‘lgan xabaringizni yuboring:\n"
        "<i>(Matn, rasm yoki video formatida yuborishingiz mumkin)</i>"
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(BroadcastSG.waiting_for_message)
async def handle_broadcast_message_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Xabar yuborish bekor qilindi.", reply_markup=remove_keyboard())
        return

    msg_type = "text"
    content = message.html_text or message.text or message.caption or ""
    photo_id = None
    video_id = None

    if message.photo:
        msg_type = "photo"
        photo_id = message.photo[-1].file_id
    elif message.video:
        msg_type = "video"
        video_id = message.video.file_id

    # Faol foydalanuvchilar sonini olamiz
    total_users = (
        await session.scalar(
            select(func.count(User.id)).where(User.is_blocked.is_(False))
        )
    ) or 0

    await state.update_data(
        msg_type=msg_type,
        content=content,
        photo_id=photo_id,
        video_id=video_id,
        total_users=total_users,
    )
    await state.set_state(BroadcastSG.confirm_broadcast)

    preview_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🚀 Yuborishni boshlash ({total_users} kishiga)",
                    callback_data="confirm_broadcast_now",
                )
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")],
        ]
    )

    await message.answer("👇 <b>Xabarning ko‘rinishi (Preview):</b>", reply_markup=remove_keyboard())

    if msg_type == "photo" and photo_id:
        await message.answer_photo(photo=photo_id, caption=content, reply_markup=preview_kb)
    elif msg_type == "video" and video_id:
        await message.answer_video(video=video_id, caption=content, reply_markup=preview_kb)
    else:
        await message.answer(text=content, reply_markup=preview_kb)


@router.callback_query(BroadcastSG.confirm_broadcast, F.data == "confirm_broadcast_now")
async def handle_confirm_broadcast(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    await state.clear()

    # DB da broadcast yaratamiz
    bc = Broadcast(
        admin_id=callback.from_user.id,
        message_type=data["msg_type"],
        content=data["content"],
        file_id=data.get("photo_id") or data.get("video_id"),
        total_users=data["total_users"],
        status="pending",
    )
    session.add(bc)
    await session.commit()

    if callback.message:
        await callback.message.answer(
            "🚀 <b>Xabar tarqatish fonda ishga tushirildi!</b>\n"
            "Tugatilgach, sizga to'liq hisobot yuboriladi.",
            reply_markup=get_admin_main_keyboard(),
        )
    await callback.answer("Boshlandi!", show_alert=False)

    # Orqa fonda vazifani ishga tushiramiz
    asyncio.create_task(
        BroadcastService.run_broadcast_task(
            bot=callback.bot,
            session_pool=async_session,
            admin_id=callback.from_user.id,
            broadcast_id=bc.id,
            message_type=data["msg_type"],
            text=data["content"],
            photo_id=data.get("photo_id"),
            video_id=data.get("video_id"),
        )
    )


# ==============================================================================
# 6. SOZLAMALAR VA MAJBURiY OBUNA (ADMIN SETTINGS)
# ==============================================================================

@router.callback_query(F.data == "admin_settings")
async def handle_admin_settings(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    sub_req = await SubscriptionService.is_subscription_required(session)
    channels = await SubscriptionService.get_active_channels(session)

    text = (
        "⚙️ <b>BOT SOZLAMALARI</b>\n\n"
        f"• Majburiy obuna rejimi: <b>{'🟢 Yoqilgan' if sub_req else '🔴 O‘chirilgan'}</b>\n"
        f"• Ulangan kanallar soni: <b>{len(channels)}</b> ta\n\n"
        "O'zgartirish uchun tugmalardan foydalaning:"
    )
    markup = get_admin_settings_keyboard(sub_req)

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "admin_toggle_sub")
async def handle_toggle_sub(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    current = await SubscriptionService.is_subscription_required(session)
    new_state = not current
    await SubscriptionService.set_subscription_required(session, new_state)
    await session.commit()

    channels = await SubscriptionService.get_active_channels(session)
    text = (
        "⚙️ <b>BOT SOZLAMALARI</b>\n\n"
        f"• Majburiy obuna rejimi: <b>{'🟢 Yoqilgan' if new_state else '🔴 O‘chirilgan'}</b>\n"
        f"• Ulangan kanallar soni: <b>{len(channels)}</b> ta\n\n"
        "Holat muvaffaqiyatli o'zgartirildi."
    )
    markup = get_admin_settings_keyboard(new_state)

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer("Sozlama saqlandi!")


@router.callback_query(F.data == "admin_channels_list")
async def handle_channels_list(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    channels = await SubscriptionService.get_active_channels(session)
    if not channels:
        text = "📢 <b>Hozircha majburiy kanallar qo‘shilmagan.</b>"
    else:
        text = "📢 <b>MAJBURiY OBUNA KANALLARI:</b>\n\n"
        for idx, ch in enumerate(channels, 1):
            text += f"{idx}. <b>{ch.title}</b> (ID: <code>{ch.channel_id}</code>)\n"

    kb = [
        [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="🔙 Sozlamalarga qaytish", callback_data="admin_settings")],
    ]
    if callback.message:
        await callback.message.edit_text(
            text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
    await callback.answer()


@router.callback_query(F.data == "admin_add_channel")
async def handle_add_channel_start(
    callback: CallbackQuery, state: FSMContext, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(AddChannelSG.waiting_for_channel_info)
    text = (
        "➕ <b>KANAL QO‘SHISH</b>\n\n"
        "Kanalni qo'shish uchun quyidagilardan birini bajaring:\n"
        "1. Kanaldan birorta xabarni bu yerga forward qiling;\n"
        "2. Yoki kanal ID sini kiriting (masalan: <code>-1001234567890</code>);\n"
        "3. Yoki kanal username'ini yuboring (masalan: <code>@UzMegaKino</code>).\n\n"
        "<i>Eslatma: Bot ushbu kanalda administrator bo'lishi shart!</i>"
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(AddChannelSG.waiting_for_channel_info)
async def handle_channel_info_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=remove_keyboard())
        return

    channel_id = None
    title = "Kanal"
    username = None
    invite_link = None

    if message.forward_from_chat:
        chat = message.forward_from_chat
        channel_id = chat.id
        title = chat.title or "Kanal"
        username = chat.username
        invite_link = chat.invite_link
    elif message.text:
        text = message.text.strip()
        try:
            chat = await message.bot.get_chat(chat_id=text)
            channel_id = chat.id
            title = chat.title or text
            username = chat.username
            invite_link = chat.invite_link
        except Exception as e:
            await message.answer(
                f"❌ Kanalni aniqlab bo'lmadi ({e}).\n"
                "Bot kanalga admin qilib tayinlanganini tekshiring va qayta yuboring:"
            )
            return

    if channel_id:
        await SubscriptionService.add_channel(
            session=session,
            channel_id=channel_id,
            title=title,
            username=username,
            invite_link=invite_link,
        )
        await session.commit()
        await state.clear()
        await message.answer(
            f"✅ <b>'{title}'</b> kanali muvaffaqiyatli qo‘shildi!",
            reply_markup=remove_keyboard(),
        )
        await message.answer("Sozlamalar:", reply_markup=get_admin_main_keyboard())


# ==============================================================================
# 7. FOYDALANUVCHILAR MA'LUMOTI (USERS INFO)
# ==============================================================================

@router.callback_query(F.data == "admin_users_info")
async def handle_admin_users_info(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    total = await session.scalar(select(func.count(User.id))) or 0
    blocked = await session.scalar(select(func.count(User.id)).where(User.is_blocked.is_(True))) or 0
    active = total - blocked

    text = (
        "👥 <b>FOYDALANUVCHILAR HAQIDA MA‘LUMOT:</b>\n\n"
        f"• Jami ro‘yxatdan o‘tganlar: <b>{total:,}</b> ta\n"
        f"• Faol obunachilar: <b>{active:,}</b> ta\n"
        f"• Botni bloklaganlar: <b>{blocked:,}</b> ta\n"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_home")]
        ]
    )
    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=kb)
    await callback.answer()


# ==============================================================================
# 8. KINO TAHRIRLASH (EDIT MOVIE)
# ==============================================================================

@router.callback_query(F.data == "admin_edit_movie")
async def handle_edit_movie_start(
    callback: CallbackQuery, state: FSMContext, db_user: User
) -> None:
    if not is_admin_check(callback.from_user.id, db_user):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(EditMovieSG.waiting_for_code)
    text = (
        "✏️ <b>KINO TAHRIRLASH</b>\n\n"
        "Tahrirlamoqchi bo‘lgan kinoning kodini yuboring:\n"
        "<i>(Masalan: 125)</i>"
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(EditMovieSG.waiting_for_code)
async def handle_edit_movie_code_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, raqamli kod kiriting:")
        return

    code = int(text)
    movie = await MovieService.get_by_code(session, code)
    if not movie:
        await message.answer(f"❌ #{code} raqamli kino topilmadi.")
        return

    await state.update_data(editing_movie_id=movie.id)
    await state.set_state(EditMovieSG.selecting_field)

    edit_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Nomi", callback_data="edit_field:title"),
                InlineKeyboardButton(text="Janri", callback_data="edit_field:genre"),
            ],
            [
                InlineKeyboardButton(text="Yili", callback_data="edit_field:year"),
                InlineKeyboardButton(text="Tili", callback_data="edit_field:language"),
            ],
            [
                InlineKeyboardButton(text="Tavsifi", callback_data="edit_field:desc"),
                InlineKeyboardButton(text="Reytingi", callback_data="edit_field:rating"),
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")],
        ]
    )

    await message.answer(
        f"🎬 <b>#{movie.code} — {movie.title}</b>\n\n"
        "Qaysi ma'lumotni o'zgartirmoqchisiz?",
        reply_markup=edit_kb,
    )


@router.callback_query(EditMovieSG.selecting_field, F.data.startswith("edit_field:"))
async def handle_edit_field_select(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    await state.update_data(edit_field_name=field)
    await state.set_state(EditMovieSG.waiting_for_new_value)

    field_labels = {
        "title": "yangi nomini",
        "genre": "yangi janrini",
        "year": "yangi yilini (masalan: 2024)",
        "language": "yangi tilini",
        "desc": "yangi tavsifini",
        "rating": "yangi reytingini (masalan: 8.5)",
    }
    label = field_labels.get(field, "yangi qiymatini")

    if callback.message:
        await callback.message.answer(
            f"✍️ Kinoning {label} kiriting:",
            reply_markup=get_cancel_keyboard(),
        )
    await callback.answer()


@router.message(EditMovieSG.waiting_for_new_value)
async def handle_edit_field_save(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.text or message.text == "❌ Bekor qilish":
        return

    data = await state.get_data()
    movie_id = data.get("editing_movie_id")
    field = data.get("edit_field_name")
    val = message.text.strip()

    update_kwargs = {}
    if field == "title":
        update_kwargs["title"] = val
    elif field == "genre":
        update_kwargs["genre"] = val
    elif field == "year":
        if val.isdigit():
            update_kwargs["year"] = int(val)
        else:
            await message.answer("⚠️ Yil raqam bo'lishi kerak!")
            return
    elif field == "language":
        update_kwargs["language"] = val
    elif field == "desc":
        update_kwargs["description"] = val
    elif field == "rating":
        try:
            update_kwargs["rating"] = float(val.replace(",", "."))
        except ValueError:
            await message.answer("⚠️ Reyting son bo'lishi kerak!")
            return

    await MovieService.update_movie(session, movie_id, **update_kwargs)
    await session.commit()
    await state.clear()

    await message.answer(
        "✅ <b>Kino ma'lumoti muvaffaqiyatli yangilandi!</b>",
        reply_markup=remove_keyboard(),
    )
    await message.answer("Admin bosh menyusi:", reply_markup=get_admin_main_keyboard())
