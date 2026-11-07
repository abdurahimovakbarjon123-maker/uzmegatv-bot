from aiogram.fsm.state import State, StatesGroup


class AddMovieSG(StatesGroup):
    """Kino qo'shish jarayoni holatlari."""
    waiting_for_title = State()
    waiting_for_genre = State()
    waiting_for_year = State()
    waiting_for_language = State()
    waiting_for_description = State()
    waiting_for_rating = State()
    waiting_for_poster = State()
    waiting_for_video = State()
    waiting_for_confirmation = State()
    # Qo'shimcha qism qo'shish
    waiting_for_additional_part = State()


class EditMovieSG(StatesGroup):
    """Kino ma'lumotlarini tahrirlash holatlari."""
    waiting_for_code = State()
    selecting_field = State()
    waiting_for_new_value = State()


class DeleteMovieSG(StatesGroup):
    """Kino o'chirish holatlari."""
    waiting_for_code = State()
    confirm_delete = State()


class BroadcastSG(StatesGroup):
    """Barcha foydalanuvchilarga xabar yuborish holatlari."""
    waiting_for_message = State()
    confirm_broadcast = State()


class AddChannelSG(StatesGroup):
    """Majburiy obuna kanalini qo'shish."""
    waiting_for_channel_info = State()


class SearchSG(StatesGroup):
    """Qidiruv holatlari."""
    waiting_for_name_query = State()
    waiting_for_year_query = State()


class ReportSG(StatesGroup):
    """Kino bo'yicha shikoyat/xatolik xabari."""
    waiting_for_text = State()
