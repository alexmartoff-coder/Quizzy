from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_payment_inline_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_quiz_flow(message: Message):
    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            f"Мы набрали {config.TICKET_LIMIT}+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    text = (
        "Каждый платёж даёт 1 гарантированный базовый билет + возможность получить "
        "до +3 бонусных билетов за хороший результат в квизе (8/9/10 правильных ответов).\n\n"
        "Стоимость участия: 99 ₽"
    )
    await message.answer(text, reply_markup=get_payment_inline_keyboard())

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_99(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("Приём заявок завершён!", show_alert=True)
        return

    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Билет на квиз iPhone 17",
            description="1 базовый билет + до 3 бонусных за квиз.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")

    await callback.answer()

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

    ticket_num = await issue_ticket(user_id, "paid")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await message.answer(
            f"✅ Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "Нажми кнопку ниже, чтобы начать квиз и получить бонусные билеты!",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании заявки. Свяжитесь с поддержкой.")

    await check_and_trigger_closure(message.bot)
