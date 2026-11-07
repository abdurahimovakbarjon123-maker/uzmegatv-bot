import math
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.inline import (
    get_movies_pagination_keyboard,
    get_search_menu_keyboard,
    get_start_inline_keyboard,
)
from bot.keyboards.reply import get_cancel_keyboard, remove_keyboard
from bot.services.movie_service import MovieService
from bot.states.states import SearchSG

router = Router(name="search_router")


@router.callback_query(F.data == "menu_search")
async def handle_search_menu(callback: CallbackQuery) -> None:
    """Kino qidiruv asosiy menyusi."""
    text = (
        "🔍 <b>UZMEGATV — KINO QIDIRUV</b>\n\n"
        "O'zingizga qulay qidiruv turini tanlang:\n"
        "• <b>Nomi bo‘yicha:</b> Kino nomini yozib qidiring\n"
        "• <b>Janrlar bo‘yicha:</b> Fantastika, Jangari, Komediya va boshqalar\n"
        "• <b>Yili bo‘yicha:</b> Chiqqan yili orqali qidiring\n\n"
        "<i>Shuningdek, shunchaki kino kodini (masalan: 125) chatga yozishingiz ham mumkin!</i>"
    )
    if callback.message:
        await callback.message.edit_text(
            text=text, reply_markup=get_search_menu_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "search_by_name")
async def handle_search_by_name_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Nom bo'yicha qidiruvni boshlash."""
    await state.set_state(SearchSG.waiting_for_name_query)
    text = (
        "🔎 <b>Kino nomini kiriting:</b>\n\n"
        "Masalan: <i>Interstellar, Forsaj, Qasoskorlar...</i>\n"
        "Kino nomining bir qismini kiritishingiz ham yetarli."
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(SearchSG.waiting_for_name_query)
async def handle_search_by_name_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Nom bo'yicha qidiruv so'rovini qabul qilish va natijalarni chiqarish."""
    if not message.text:
        return
    query = message.text.strip()
    if query == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "Qidiruv bekor qilindi.", reply_markup=remove_keyboard()
        )
        await message.answer(
            "Asosiy menyu:", reply_markup=get_start_inline_keyboard()
        )
        return

    await state.clear()
    page_size = settings.ITEMS_PER_PAGE
    movies, total = await MovieService.search_movies(
        session=session, query=query, page=1, page_size=page_size
    )

    if not movies:
        text = (
            f"❌ <b>'{query}'</b> bo‘yicha hech qanday kino topilmadi.\n\n"
            "• Nomni to'g'ri yozganingizni tekshiring\n"
            "• Yoki janrlar bo'yicha qidirib ko'ring"
        )
        await message.answer(text=text, reply_markup=remove_keyboard())
        await message.answer(
            "Qidiruv bo'limi:", reply_markup=get_search_menu_keyboard()
        )
        return

    total_pages = math.ceil(total / page_size)
    text = (
        f"🔍 <b>'{query}'</b> bo‘yicha qidiruv natijalari:\n"
        f"Jami topildi: <b>{total}</b> ta kino.\n"
        "Ko‘rish uchun kerakli kinoni tanlang:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=1, total_pages=total_pages, prefix="catalog"
    )
    await message.answer(text=text, reply_markup=remove_keyboard())
    await message.answer(text="Kinolar ro'yxati:", reply_markup=markup)


@router.callback_query(F.data == "search_genres_list")
async def handle_genres_list(callback: CallbackQuery, session: AsyncSession) -> None:
    """Mavjud barcha janrlarni tugmalar ko'rinishida chiqarish."""
    genres = await MovieService.get_all_genres(session)
    if not genres:
        await callback.answer("Hozircha janrlar mavjud emas!", show_alert=True)
        return

    keyboard = []
    row = []
    for g in genres:
        row.append(
            InlineKeyboardButton(text=f"🎭 {g}", callback_data=f"filter_genre:{g}")
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu_search")
    ])

    text = "🎭 <b>O‘zingizga yoqqan janrni tanlang:</b>"
    if callback.message:
        await callback.message.edit_text(
            text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_genre:"))
async def handle_filter_by_genre(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Tanlangan janr bo'yicha kinolar ro'yxati."""
    genre = callback.data.split(":")[1]
    page_size = settings.ITEMS_PER_PAGE
    movies, total = await MovieService.search_movies(
        session=session, genre=genre, page=1, page_size=page_size
    )

    if not movies:
        await callback.answer(f"{genre} janrida kinolar topilmadi!", show_alert=True)
        return

    total_pages = math.ceil(total / page_size)
    text = (
        f"🎭 <b>{genre}</b> janridagi kinolar:\n"
        f"Jami topildi: <b>{total}</b> ta kino.\n"
        "Tanlang:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=1, total_pages=total_pages, prefix="catalog"
    )
    if callback.message:
        await callback.message.edit_text(text=text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "search_by_year")
async def handle_search_by_year_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Yil bo'yicha qidiruvni boshlash."""
    await state.set_state(SearchSG.waiting_for_year_query)
    text = (
        "📅 <b>Kino chiqqan yilini kiriting:</b>\n\n"
        "Masalan: <code>2024</code> yoki <code>2019</code>"
    )
    if callback.message:
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(SearchSG.waiting_for_year_query)
async def handle_search_by_year_input(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Yil kiritilganda qidirish."""
    if not message.text:
        return
    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Qidiruv bekor qilindi.", reply_markup=remove_keyboard())
        return

    if not text.isdigit() or len(text) != 4:
        await message.answer("⚠️ Iltimos, to'g'ri 4 xonali yil kiriting (masalan: 2024):")
        return

    year = int(text)
    await state.clear()

    page_size = settings.ITEMS_PER_PAGE
    movies, total = await MovieService.search_movies(
        session=session, year=year, page=1, page_size=page_size
    )

    if not movies:
        await message.answer(
            f"❌ <b>{year}-yilda</b> chiqqan kinolar bazamizda topilmadi.",
            reply_markup=remove_keyboard(),
        )
        return

    total_pages = math.ceil(total / page_size)
    response_text = (
        f"📅 <b>{year}-yilda</b> chiqqan kinolar:\n"
        f"Jami: <b>{total}</b> ta kino.\n"
        "Tanlang:"
    )
    markup = get_movies_pagination_keyboard(
        movies, current_page=1, total_pages=total_pages, prefix="catalog"
    )
    await message.answer(text=response_text, reply_markup=remove_keyboard())
    await message.answer(text="Kinolar ro'yxati:", reply_markup=markup)
