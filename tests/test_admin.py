import pytest

from bot.config import settings
from bot.database.models import Movie, User
from bot.handlers.admin import is_admin_check
from bot.services.stats_service import StatsService


def test_admin_permission_check():
    """Admin huquqlarini tekshirish mantiqi testi."""
    admin_user = User(telegram_id=123456789, is_admin=True)
    sample_user = User(telegram_id=999888777, is_admin=False)

    settings.ADMIN_IDS = [123456789]

    # settings.ADMIN_IDS dagi foydalanuvchi
    assert is_admin_check(123456789, admin_user) is True
    # Bazada is_admin=True bo'lgan foydalanuvchi
    assert is_admin_check(555555, User(telegram_id=555555, is_admin=True)) is True
    # Oddiy foydalanuvchi
    assert is_admin_check(999888777, sample_user) is False


def test_format_dashboard_text():
    """Statistika ma'lumotlarini o'zbekcha chiroyli hisobot ko'rinishiga keltirish testi."""
    top_movie = Movie(code=125, title="Interstellar", views_count=450)
    mock_stats = {
        "total_users": 15000,
        "new_users_today": 120,
        "dau": 3400,
        "wau": 8900,
        "mau": 14200,
        "total_movies": 1250,
        "total_requests": 38900,
        "top_movies": [top_movie],
    }

    report = StatsService.format_dashboard_text(mock_stats)

    assert "UZMEGATV — TIZIM STATISTIKASI" in report
    assert "15,000" in report
    assert "120" in report
    assert "3,400" in report
    assert "Interstellar" in report
    assert "450 marta" in report
