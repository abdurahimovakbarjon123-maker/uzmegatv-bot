from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import BotSetting, User
from bot.keyboards.inline import get_start_inline_keyboard
from bot.keyboards.reply import remove_keyboard
from bot.utils.helpers import extract_movie_code_from_deeplink

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start_command(
    message: Message, session: AsyncSession, db_user: User
) -> None:
    """
    /start buyrug'ini qabul qilish.
    Agar deep-link parametri (masalan, /start movie_125) bo'lsa,
    to'g'ridan-to'g'ri o'sha kinoni yuklab berishga yo'naltiriladi.
    """
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        deep_arg = args[1].strip()
        code = extract_movie_code_from_deeplink(deep_arg)
        if code:
            # Kinoni yetkazish handleriga virtual yo'naltirish
            from bot.handlers.movies import deliver_movie_by_code
            await deliver_movie_by_code(message, session, code, db_user=db_user)
            return

    # Standart tabrik matni
    welcome_text = (
        "🎬 <b>UZMEGATV — Kino olamiga xush kelibsiz!</b>\n\n"
        "🍿 Sevimli kinolaringizni biz bilan yuqori sifatda tomosha qiling.\n\n"
        "🔢 <b>Kino kodini yuboring</b> va kerakli kinoni bir zumda oling!\n"
        "<i>Masalan: 1, 125 yoki 1000</i>"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_start_inline_keyboard(),
    )


@router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery) -> None:
    """Asosiy menyuga qaytish callbacki."""
    welcome_text = (
        "🎬 <b>UZMEGATV — Asosiy menyu</b>\n\n"
        "🍿 Sevimli kinolaringizni biz bilan tomosha qiling.\n\n"
        "🔢 <b>Kino kodini yuboring</b> va kerakli kinoni oling!"
    )
    if callback.message:
        await callback.message.edit_text(
            text=welcome_text,
            reply_markup=get_start_inline_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "menu_help")
async def handle_help_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Yordam va qo'llanma bo'limi."""
    contact_setting = await session.scalar(
        select(BotSetting.value).where(BotSetting.key == "support_contact")
    )
    admin_contact = contact_setting or "@abdurahimoovvvv"

    help_text = (
        "📞 <b>UZMEGATV — Yordam va Qo‘llanma</b>\n\n"
        "📌 <b>Botdan qanday foydalaniladi?</b>\n"
        "1. Kanalimizdagi postlarda ko‘rsatilgan kino kodini eslab qoling.\n"
        "2. Botga o‘sha raqamni (masalan: <code>125</code>) yuboring.\n"
        "3. Bot sizga kinoni va barcha ma'lumotlarini taqdim etadi.\n\n"
        "🔍 <b>Qidiruv:</b>\n"
        "Agar kino kodini bilmasangiz, <b>'🔎 Kino qidirish'</b> tugmasini bosing va nomini kiriting.\n\n"
        "⚖️ <b>Mualliflik huquqi:</b>\n"
        "Botda faqat ommaviy ruxsat berilgan yoki operator huquqiga ega materiallar taqdim etiladi.\n\n"
        f"👨‍💻 <b>Admin bilan aloqa:</b> {admin_contact}"
    )
    if callback.message:
        await callback.message.edit_text(
            text=help_text,
            reply_markup=get_start_inline_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery) -> None:
    """Passiv sahifa ko'rsatkichi tugmasi."""
    await callback.answer()
