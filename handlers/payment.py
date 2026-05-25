from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_quiz_flow(message: Message):
    from database.db import has_accepted_rules
    if not await has_accepted_rules(message.from_user.id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        closure_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await message.answer(closure_text)
        return

    description = (
        "Покажи свои знания об Apple и выиграй iPhone 17 PRO 256 Гб!\n\n"
        "💳 Стоимость участия: 99 ₽\n"
        "🎫 За участие ты получаешь 1 гарантированный билет.\n"
        "🎁 Дополнительно можно получить до +3 бонусных билетов за отличный результат в квизе:\n"
        "• 10 правильных ответов: +3 билета\n"
        "• 9 правильных ответов: +2 билета\n"
        "• 8 правильных ответов: +1 билет"
    )

    try:
        await message.answer(description)
        await message.answer_invoice(
            title="Участие в квизе iPhone 17",
            description="1 базовый билет + бонусы за квиз",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await message.answer(f"❌ Ошибка при формировании счёта: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    user = message.from_user

    await add_user(user_id, user.username, user.full_name)

    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await message.answer(
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\nНажми кнопку ниже, чтобы начать квиз и получить бонусные билеты!",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании билета. Пожалуйста, обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
