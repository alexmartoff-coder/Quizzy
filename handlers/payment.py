from aiogram import Router, F
from aiogram.types import Message
from database.db import issue_ticket, set_quiz_session, is_collection_closed
from keyboards.menu import get_start_quiz_keyboard

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🆓 Бесплатная заявка на участие")
async def start_free_attempt(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer("🎉 Приём заявок завершён!")
        return

    from database.db import has_user_used_free_attempt
    if await has_user_used_free_attempt(user_id):
        await message.answer("Вы уже использовали свою бесплатную попытку.")
        return

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await message.answer(
            f"✅ Ваша заявка №{ticket_num:05d} создана.\n\nГотовы пройти квиз?",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании заявки.")
