import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers import base, payment, quiz, admin

# YOOKASSA TEST INTEGRATION: Логирование в консоль
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры. Важно: платежный роутер (payment) должен быть одним из первых
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(base.router)
    dp.include_router(quiz.router)

    logging.info("Starting @googlestop_bot...")

    # Автоматически определяем необходимые типы обновлений (включая pre_checkout_query и successful_payment)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
