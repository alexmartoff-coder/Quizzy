from aiogram import Router, F, Bot
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, ContentType
from database.db import issue_ticket, set_quiz_session, is_collection_closed, log_payment
from keyboards.menu import get_start_quiz_keyboard
from config import PAYMENT_PROVIDER_TOKEN

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def process_play_button(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    await message.answer_invoice(
        title="Участие в квизе за iPhone 17",
        description="1 базовый билет + до 3 бонусных билетов за результат в квизе.",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Участие", amount=9900)], # 99.00 RUB
        payload=f"quiz_payment_{user_id}",
        start_parameter="quiz_payment"
    )

@payment_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    if await is_collection_closed():
        await pre_checkout_query.answer(ok=False, error_message="Извините, сбор билетов уже завершен.")
        return
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    sp = message.successful_payment

    await log_payment(
        user_id=user_id,
        amount=sp.total_amount // 100,
        payload=sp.invoice_payload,
        telegram_id=sp.telegram_payment_charge_id,
        provider_id=sp.provider_payment_charge_id
    )

    ticket_num = await issue_ticket(user_id, "paid")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await message.answer(
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\nГотовы пройти квиз?",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании билета. Обратитесь в поддержку.")

@payment_router.message(F.text == "🆓 Бесплатная заявка на участие")
async def start_free_attempt(message: Message):
    # This button is removed from keyboard, but handler kept for compatibility if needed or to show message
    await message.answer("Бесплатные попытки закончились или недоступны. Используйте платную версию для участия!")
