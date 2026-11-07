import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import settings
from bot.database.session import close_db, init_db
from bot.handlers import setup_routers
from bot.middlewares.db import DatabaseMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.user_tracker import UserTrackerMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("UZMEGATV")


async def create_storage():
    """FSM Storage yaratish (Redis mavjud bo'lsa Redis, aks holda MemoryStorage)."""
    if settings.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(settings.REDIS_URL)
            logger.info("Redis storage muvaffaqiyatli ulandi.")
            return storage
        except Exception as e:
            logger.warning(f"Redis ulanishida xatolik ({e}), MemoryStorage ishlatiladi.")
    return MemoryStorage()


async def main() -> None:
    """Botni ishga tushirishning asosiy nuqtasi."""
    logger.info("UZMEGATV boti ishga tushirilmoqda...")

    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    await init_db()

    # 2. Storage
    storage = await create_storage()

    # 3. Bot va Dispatcher obyektlari
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # 4. Middleware-larni ro'yxatdan o'tkazish
    dp.update.middleware(DatabaseMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(UserTrackerMiddleware())
    dp.callback_query.middleware(UserTrackerMiddleware())

    # 5. Handler routerlarini ulash
    setup_routers(dp)

    port_env = os.getenv("PORT")
    web_runner = None

    try:
        try:
            bot_info = await bot.get_me()
            logger.info(f"Bot ma'lumotlari olindi: @{bot_info.username} (ID: {bot_info.id})")
        except TelegramUnauthorizedError:
            logger.critical(
                "\n"
                "=====================================================================\n"
                "❌ XATOLIK: Telegram bot tokeni noto'g'ri (Unauthorized)!\n"
                "====================================================================="
            )
            return

        # Agar PORT berilgan bo'lsa (Render buluti) -> Webhook rejimida ishlaymiz
        if port_env:
            port = int(port_env)
            base_url = os.getenv("RENDER_EXTERNAL_URL", "https://uzmegatv-bot.onrender.com").rstrip("/")
            webhook_url = f"{base_url}/webhook"

            app = web.Application()

            async def ping_handler(request):
                return web.Response(text="UZMEGATV bot is running 24/7!")

            app.router.add_get("/", ping_handler)
            app.router.add_get("/health", ping_handler)

            SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
            setup_application(app, dp, bot=bot)

            web_runner = web.AppRunner(app)
            await web_runner.setup()
            site = web.TCPSite(web_runner, "0.0.0.0", port)
            await site.start()

            logger.info(f"Health-check va Webhook server {port}-portda ishga tushdi.")
            logger.info(f"Telegram Webhook sozlanmoqda: {webhook_url}")
            await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            logger.info(f"✅ Bot Webhook rejimida 24/7 internetda to'liq ishga tushdi!")

            # Server to'xtatilguncha kutib turamiz
            stop_event = asyncio.Event()
            await stop_event.wait()

        else:
            # Lokal kompyuterda ishga tushirilganda -> Polling rejimi
            logger.info("Lokal rejim: Polling ishga tushirilmoqda...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
    finally:
        logger.info("Resurslar tozalanmoqda...")
        if web_runner:
            try:
                await web_runner.cleanup()
            except Exception:
                pass
        await close_db()
        await bot.session.close()
        logger.info("Bot to'liq to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Dastur yakunlandi.")