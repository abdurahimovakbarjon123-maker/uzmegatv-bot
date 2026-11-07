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


async def start_health_server(port: int) -> web.AppRunner:
    """Render kabi bulut platformalarida botni 24/7 ushlab turish uchun health server."""
    app = web.Application()

    async def ping_handler(request):
        return web.Response(text="UZMEGATV bot is running 24/7!")

    app.router.add_get("/", ping_handler)
    app.router.add_get("/health", ping_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check web server {port}-portda muvaffaqiyatli ishga tushdi.")
    return runner


async def main() -> None:
    """Botni ishga tushirishning asosiy nuqtasi."""
    logger.info("UZMEGATV boti ishga tushirilmoqda...")

    # Render yoki boshqa platforma PORT bergan bo'lsa, health server yoqamiz
    port_env = os.getenv("PORT")
    health_runner = None
    if port_env:
        try:
            health_runner = await start_health_server(int(port_env))
        except Exception as e:
            logger.warning(f"Health web serverni ishga tushirishda xatolik: {e}")

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

    # 6. Botni ishga tushirish va polling
    try:
        try:
            bot_info = await bot.get_me()
            logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} (ID: {bot_info.id})")
        except TelegramUnauthorizedError:
            logger.critical(
                "\n"
                "=====================================================================\n"
                "❌ XATOLIK: Telegram bot tokeni noto'g'ri (Unauthorized)!\n"
                "Kiritilgan token Telegram serveri tomonidan qabul qilinmadi.\n"
                "Sabablar:\n"
                "1. Token nusxalanganda qaysidir harf yoki raqam tushib qolgan.\n"
                "2. BotFather'da ushbu bot o'chirilgan yoki tokeni yangilangan (Revoke qilingan).\n\n"
                "Yechim: @BotFather ga kirib /mybots -> Botingizni tanlang -> 'API Token'ni\n"
                "qayta oling va .env faylidagi BOT_TOKEN ga to'g'ri qo'ying.\n"
                "====================================================================="
            )
            return

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
    finally:
        logger.info("Resurslar tozalanmoqda...")
        if health_runner:
            try:
                await health_runner.cleanup()
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