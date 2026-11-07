from aiogram import Dispatcher

from bot.handlers.admin import router as admin_router
from bot.handlers.favorites import router as favorites_router
from bot.handlers.movies import router as movies_router
from bot.handlers.search import router as search_router
from bot.handlers.start import router as start_router


def setup_routers(dp: Dispatcher) -> None:
    """Barcha routerlarni to'g'ri tartibda dispatcherga ulash."""
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(favorites_router)
    dp.include_router(search_router)
    dp.include_router(movies_router)
