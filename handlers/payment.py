from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import TICKET_LIMIT, CHANNEL_ID, OWNER_ID
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection, check_and_trigger_closure
from keyboards.menu import get_start_quiz_keyboard
import logging

router = Router()

# --- ГЛАВНЫЕ КОМАНДЫ ---

@router.message(F.text == "🎁 Участвовать в розыгрыше iPhone 17 PRO 256 Гб.")
async def cmd_play(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 PRO 256 Гб. состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    # Сразу выдаем билет и готовим квиз (без оплаты)
    logging.info(f"PARTICIPATE: User {user_id} joined without payment")

    await issue_random_tickets(user_id, 1, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer(
        "✅ Ты успешно зарегистрирован в розыгрыше!\n\n"
        "Тебе выдан 1 основной билет. Теперь ты можешь пройти квиз и получить до 3-х бонусных билетов!\n\n"
        "Начинаем?",
        reply_markup=get_start_quiz_keyboard()
    )

    # Проверка лимита после выдачи билета
    await check_and_trigger_closure(message.bot)

