import math
from typing import Optional, Union
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import User
from bot.keyboards.inline import (
    get_movie_inline_keyboard,
    get_movies_pagination_keyboard,
    get_start_inline_keyboard,
    get_subscription_keyboard,
)
from bot.services.movie_service import MovieService
from bot.services.subscription_service import SubscriptionService
from bot.states.states import ReportSG
from bot.utils.helpers import format_movie_caption

router = Router(name="movies_router")


async def deliver_movie_by_code(
    event: Union[Message, CallbackQuery],
    session: AsyncSession,
    code: int,
    db_user: User,
    part_number: int = 1,
) -> None:
    """
    Kino kodini tekshirib, uni foydalanuvchiga taqdim etuvchi markaziy funksiya.
    Obuna holati, sevimli holati va ko'p qismlilik to'liq qo'llab-quvvatlanadi.
    """
    bot = event.bot
    user_id = event.from_user.id
    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id

    # 1. Majburiy kanal obunasini tekshirish
    is_subscribed, missing_channels = await SubscriptionService.check_user_subscription(
        bot=bot, session=session, user_id=user_id
    )

    if not is_subscribed:
        sub_text = (
            "⚠️ <b>Diqqat! Kinoni ko‘rish uchun quyidagi kanallarga a‘zo bo‘lishingiz shart:</b>\n\n"
            "Iltimos, a'zo bo'lib <b>'✅ Tekshirish'</b> tugmasini bosing."
        )
        markup = get_subscription_keyboard(missing_channels, target_code=code)
        if isinstance(event, CallbackQuery) and event.message:
            await event.message.answer(text=sub_text, reply_markup=markup)
            await event.answer()
        else:
            await event.answer(text=sub_text, reply_markup=markup)
        return

    # 2. Kinoni bazadan qidirish
    movie = await MovieService.get_by_code(session, code)

    if not movie:
        not_found_text = (
            f"❌ <b>#{code} raqamli kino topilmadi!</b>\n\n"
            "Iltimos, kodni to'g'ri kiritganingizga ishonch hosil qiling.\n"
            "Kino nomini bilish uchun qidiruvdan foydalanishingiz mumkin."
        )
        if isinstance(event, CallbackQuery):
            await event.answer("Kino topilmadi!", show_alert=True)
            if event.message:
                await event.message.answer(
                    text=not_found_text, reply_markup=get_start_inline_keyboard()
                )
        else:
            await event.answer(
                text=not_found_text, reply_markup=get_start_inline_keyboard()
            )
        # So'rovni topilmagan sifatida qayd etamiz
        await MovieService.record_movie_request(
            session=session,
            query=str(code),
            user_id=db_user.id if db_user else None,
            matched_movie_id=None,
        )
        return

    # 3. So'rovni va tomosha tarixini qayd etish
    await MovieService.record_movie_request(
        session=session,
        query=str(code),
        user_id=db_user.id if db_user else None,
        matched_movie_id=movie.id,
    )

    # 4. Sevimlilar holati
    is_fav = False
    if db_user:
        is_fav = await MovieService.is_favorite(session, db_user.id, movie.id)

    # 5. Qismni aniqlash
    files = movie.files
    selected_file = None
    if files:
        for f in files:
            if f.part_number == part_number:
                selected_file = f
                break
        if not selected_file:
            selected_file = files[0]

    part_info = (
        f"{selected_file.part_name or f'{selected_file.part_number}-qism'}"
        if (files and len(files) > 1 and selected_file)
        else None
    )

    bot_info = await bot.get_me()
    active_bot_username = bot_info.username or settings.BOT_USERNAME or "uz_megatv_bot"
    caption = format_movie_caption(movie, part_info=part_info, bot_username=active_bot_username)
    markup = get_movie_inline_keyboard(
        movie=movie,
        is_fav=is_fav,
        current_part=selected_file.part_number if selected_file else 1,
        files=files,
        bot_username=active_bot_username,
    )

    # 6. Faylni yuborish
    if selected_file:
        try:
            if selected_file.file_type == "video":
                await bot.send_video(
                    chat_id=chat_id,
                    video=selected_file.file_id,
                    caption=caption,
                    reply_markup=markup,
                )
            else:
                await bot.send_document(
                    chat_id=chat_id,
                    document=selected_file.file_id,
                    caption=caption,
                    reply_markup=markup,
                )
        except TelegramBadRequest as e:
            # Agar Telegram file_id muddati o'tgan bo'lsa yoki xatolik bersa
            await bot.send_message(
                chat_id=chat_id,
                text=f"{caption}\n\n⚠️ <i>Video faylni yuklashda xatolik yuz berdi. Tez orada tuzatiladi.</i>",
                reply_markup=markup,
            )
    elif movie.poster_file_id:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=movie.poster_file_id,
                caption=caption,
                reply_markup=markup,
            )
        except Exception:
            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=markup)
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=markup)

    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(F.text.regexp(r"^\d+$"))
async def handle_numeric_movie_code(
    message: Message, session: AsyncSession, db_user: User
) -> None:
    """Foydalanuvchi to'g'ridan-to'g'ri raqamli kino kodini yuborganda."""
    if not message.text:
        return
    code = int(message.text.strip())
    await deliver_movie_by_code(message, session, code, db_user=db_user)


@router.callback_query(F.data.startswith("show_movie:"))
async def handle_show_movie_callback(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Inline tugma orqali kinoni tanlash."""
    code_str = callback.data.split(":")[1]
    if code_str.isdigit():
        code = int(code_str)
        await deliver_movie_by_code(callback, session, code, db_user=db_user)


@router.callback_query(F.data.startswith("movie_part:"))
async def handle_movie_part_callback(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Kinoning boshqa qismini tanlash."""
    parts = callback.data.split(":")
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        code = int(parts[1])
        part_num = int(parts[2])
        await deliver_movie_by_code(
            callback, session, code, db_user=db_user, part_number=part_num
        )


@router.callback_query(F.data == "random_movie")
async def handle_random_movie_callback(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tasodifiy kino tanlash."""
    movie = await MovieService.get_random_movie(session)
    if not movie:
        await callback.answer("Hozircha bazada kinolar mavjud emas!", show_alert=True)
        return
    await deliver_movie_by_code(callback, session, movie.code, db_user=db_user)


@router.callback_query(F.data.startswith("catalog:"))
async def handle_catalog_pagination(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Kinolar katalogi sahifalari."""
    page_str = callback.data.split(":")[1]
    page = int(page_str) if page_str.isdigit() else 1
    page_size = settings.ITEMS_PER_PAGE

    movies, total = await MovieService.get_movies_paginated(
        session, page=page, page_size=page_size, order_by="code"
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    text = (
        "🎬 <b>UZMEGATV — KINOLAR KATALOGI</b>\n\n"
        f"Jami mavjud kinolar: <b>{total}</b> ta\n"
        "O'zingizga yoqqan kinoni tanlang yoki uning kodini yuboring:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=page, total_pages=total_pages, prefix="catalog"
    )

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("top_movies:"))
async def handle_top_movies_pagination(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Eng mashhur (TOP) kinolar."""
    page_str = callback.data.split(":")[1]
    page = int(page_str) if page_str.isdigit() else 1
    page_size = settings.ITEMS_PER_PAGE

    movies, total = await MovieService.get_movies_paginated(
        session, page=page, page_size=page_size, order_by="popular"
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    text = (
        "🔥 <b>UZMEGATV — ENG KO‘P KO‘RILGAN TOP KINOLAR</b>\n\n"
        f"Foydalanuvchilarimiz eng ko'p tomosha qilgan kinolar:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=page, total_pages=total_pages, prefix="top_movies"
    )

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("new_movies:"))
async def handle_new_movies_pagination(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Yangi qo'shilgan kinolar."""
    page_str = callback.data.split(":")[1]
    page = int(page_str) if page_str.isdigit() else 1
    page_size = settings.ITEMS_PER_PAGE

    movies, total = await MovieService.get_movies_paginated(
        session, page=page, page_size=page_size, order_by="newest"
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    text = (
        "🆕 <b>UZMEGATV — ENG SO‘NGGI QO‘SHILGAN KINOLAR</b>\n\n"
        f"Bazamizga oxirgi bo'lib qo'shilgan kinolar ro'yxati:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=page, total_pages=total_pages, prefix="new_movies"
    )

    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("check_sub:"))
async def handle_check_subscription_callback(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Obunani tekshirish tugmasi."""
    bot = callback.bot
    user_id = callback.from_user.id
    target = callback.data.split(":")[1]

    is_sub, missing = await SubscriptionService.check_user_subscription(
        bot=bot, session=session, user_id=user_id
    )

    if is_sub:
        await callback.answer("✅ Rahmat! Obuna muvaffaqiyatli tasdiqlandi.", show_alert=True)
        if target.isdigit():
            code = int(target)
            await deliver_movie_by_code(callback, session, code, db_user=db_user)
        else:
            if callback.message:
                await callback.message.edit_text(
                    text="🎬 <b>Obuna tasdiqlandi!</b>\n\nKino kodini yuboring yoki quyidagi menyudan foydalaning:",
                    reply_markup=get_start_inline_keyboard(),
                )
    else:
        await callback.answer(
            "❌ Siz hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, a'zo bo'ling.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("report_movie:"))
async def handle_report_movie_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Kino haqida shikoyat / xatolik bildirish."""
    movie_id_str = callback.data.split(":")[1]
    if movie_id_str.isdigit():
        await state.update_data(reporting_movie_id=int(movie_id_str))
        await state.set_state(ReportSG.waiting_for_text)
        if callback.message:
            await callback.message.answer(
                "✍️ <b>Kino haqida xabar bering:</b>\n\n"
                "Qanday muammo yuz berdi? (Masalan: video ochilmayapti, ovozi yo'q, xato qism).\n"
                "Xabaringizni yozib yuboring (yoki bekor qilish uchun /cancel bosing):"
            )
        await callback.answer()


@router.message(ReportSG.waiting_for_text)
async def handle_report_text(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Foydalanuvchi shikoyat matnini qabul qilish va adminga yuborish."""
    if not message.text:
        return
    data = await state.get_data()
    movie_id = data.get("reporting_movie_id")
    movie = await MovieService.get_by_id(session, movie_id) if movie_id else None

    # Adminga xabar yo'llash
    movie_info = f"#{movie.code} - {movie.title}" if movie else f"ID: {movie_id}"
    admin_msg = (
        "⚠️ <b>YANGI SHIKOYAT / XATOLIK BILDIRIShI:</b>\n\n"
        f"🎬 Kino: <b>{movie_info}</b>\n"
        f"👤 Yuboruvchi: @{message.from_user.username or 'yo‘q'} (ID: {message.from_user.id})\n"
        f"📝 Xabar: <i>{message.text}</i>"
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            await message.bot.send_message(chat_id=admin_id, text=admin_msg)
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ <b>Xabaringiz qabul qilindi!</b>\nAdminlarimiz tez orada muammoni bartaraf etishadi. Rahmat!"
    )
