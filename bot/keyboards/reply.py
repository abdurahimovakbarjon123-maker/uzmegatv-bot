from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish uchun qulay pastki klaviatura."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_skip_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Ixtiyoriy qadamlar uchun (o'tkazib yuborish yoki bekor qilish)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➡️ O‘tkazib yuborish"),
                KeyboardButton(text="❌ Bekor qilish"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Pastki klaviaturani tozalash."""
    return ReplyKeyboardRemove()
