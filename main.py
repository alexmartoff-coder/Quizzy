import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers import base, quiz, admin

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

    # РЕГИСТРАЦИЯ РОУТЕРОВ
    dp.include_router(admin.router)
    dp.include_router(base.router)
    dp.include_router(quiz.router)


    logging.info("Starting @googlestop_bot...")

    # Сброс вебхуков перед началом поллинга для избежания Conflict
    await bot.delete_webhook(drop_pending_updates=True)

    # Автоматически определяем типы обновлений, которые бот должен слушать
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
