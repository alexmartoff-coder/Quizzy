import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers import base, payment, quiz

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Платежный роутер регистрируем ПЕРВЫМ
    dp.include_router(payment.router)
    dp.include_router(base.router)
    dp.include_router(quiz.router)

    logging.info("Starting bot...")

    # Автоматическое определение необходимых типов обновлений (включая pre_checkout_query)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
