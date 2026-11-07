from unittest.mock import MagicMock
from aiogram.exceptions import TelegramBadRequest

from bot.database.models import RequiredChannel
from bot.services.subscription_service import SubscriptionService


def run_coro(coro):
    """Event loop sockets talab qilmaydigan tezkor korutina bajaruvchi."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    raise RuntimeError("Korutina to'liq yakunlanmadi")


def test_subscription_disabled_allows_all():
    """Majburiy obuna o'chirilgan bo'lsa barcha foydalanuvchilar o'tishi kerak."""
    async def fake_is_sub_req(session):
        return False

    original_is_sub = SubscriptionService.is_subscription_required
    try:
        SubscriptionService.is_subscription_required = fake_is_sub_req
        is_sub, missing = run_coro(
            SubscriptionService.check_user_subscription(bot=None, session=None, user_id=12345)
        )
        assert is_sub is True
        assert len(missing) == 0
    finally:
        SubscriptionService.is_subscription_required = original_is_sub


def test_subscription_active_user_is_member():
    """Foydalanuvchi a'zo bo'lganda muvaffaqiyatli tekshirish."""
    async def fake_is_sub_req(session):
        return True

    channel = RequiredChannel(channel_id=-1001, title="Kanal 1")
    async def fake_get_channels(session):
        return [channel]

    mock_bot = MagicMock()
    mock_member = MagicMock()
    mock_member.status = "member"

    async def fake_get_chat_member(chat_id, user_id):
        return mock_member

    mock_bot.get_chat_member = fake_get_chat_member

    original_is_sub = SubscriptionService.is_subscription_required
    original_get_ch = SubscriptionService.get_active_channels
    try:
        SubscriptionService.is_subscription_required = fake_is_sub_req
        SubscriptionService.get_active_channels = fake_get_channels

        is_sub, missing = run_coro(
            SubscriptionService.check_user_subscription(bot=mock_bot, session=None, user_id=12345)
        )
        assert is_sub is True
        assert len(missing) == 0
    finally:
        SubscriptionService.is_subscription_required = original_is_sub
        SubscriptionService.get_active_channels = original_get_ch


def test_subscription_active_user_not_member():
    """Foydalanuvchi a'zo bo'lmaganda unjoined kanallar qaytishi kerak."""
    async def fake_is_sub_req(session):
        return True

    channel = RequiredChannel(channel_id=-1001, title="Kanal 1")
    async def fake_get_channels(session):
        return [channel]

    mock_bot = MagicMock()
    mock_member = MagicMock()
    mock_member.status = "left"

    async def fake_get_chat_member(chat_id, user_id):
        return mock_member

    mock_bot.get_chat_member = fake_get_chat_member

    original_is_sub = SubscriptionService.is_subscription_required
    original_get_ch = SubscriptionService.get_active_channels
    try:
        SubscriptionService.is_subscription_required = fake_is_sub_req
        SubscriptionService.get_active_channels = fake_get_channels

        is_sub, missing = run_coro(
            SubscriptionService.check_user_subscription(bot=mock_bot, session=None, user_id=12345)
        )
        assert is_sub is False
        assert len(missing) == 1
        assert missing[0].channel_id == -1001
    finally:
        SubscriptionService.is_subscription_required = original_is_sub
        SubscriptionService.get_active_channels = original_get_ch
