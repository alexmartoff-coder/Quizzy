import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers import base, payment, quiz, admin

# Расширенное логирование в консоль и файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

async def main():
    # Инициализация БД
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(base.router)
    dp.include_router(quiz.router)

    from config import YOOKASSA_PROVIDER_TOKEN
    if not YOOKASSA_PROVIDER_TOKEN or YOOKASSA_PROVIDER_TOKEN == "YOUR_YOOKASSA_TOKEN":
        logging.warning("⚠️ YOOKASSA_PROVIDER_TOKEN is missing or not set!")
    else:
        logging.info(f"✅ YooKassa token loaded (prefix: {YOOKASSA_PROVIDER_TOKEN[:10]}...)")

    logging.info("Starting @googlestop_bot...")

    # Явно указываем типы обновлений для polling
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query", "successful_payment"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
