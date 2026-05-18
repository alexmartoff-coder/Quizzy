from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, add_system_log
from keyboards.menu import get_start_quiz_keyboard
import config

payment_router = Router(name="payment_router")

@payment_router.message(F.text.contains("Участвовать") | F.text.contains("Играть в квиз"))
async def start_payment(message: Message):
    user_id = message.from_user.id
    print(f"💰 PAYMENT START | User: {user_id}")

    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await add_system_log(user_id, "PAYMENT_START_TRIGGERED")

    if await is_collection_closed():
        print(f"❌ PAYMENT REJECTED (CLOSED) | User: {user_id}")
        await message.answer("🎉 Сбор билетов завершён досрочно! Мы набрали 3500+ билетов.")
        return

    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        token = str(config.YOOKASSA_PROVIDER_TOKEN)
        await message.answer_invoice(
            title="Билет участия в розыгрыше",
            description="1 билет + доступ к квизу за iPhone 17 PRO 256 Гб.",
            provider_token=token,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=9900)],
            payload="ticket_purchase",
            start_parameter="pay_ticket"
        )
        print(f"🚀 INVOICE SENT | User: {user_id}")
        await add_system_log(user_id, "INVOICE_SENT_SUCCESS")
    except Exception as e:
        print(f"❌ INVOICE ERROR | User: {user_id} | {e}")
        await add_system_log(user_id, "INVOICE_ERROR", str(e))
        await message.answer(f"❌ Ошибка при формировании счёта: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    user_id = pre_checkout_query.from_user.id
    print(f"✅ PRE_CHECKOUT_QUERY RECEIVED | User: {user_id}")
    await add_system_log(user_id, "PRE_CHECKOUT_RECEIVED")
    await pre_checkout_query.answer(ok=True)
    print(f"🆗 PRE_CHECKOUT_QUERY ANSWERED OK | User: {user_id}")

@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    print(f"🎉 SUCCESSFUL PAYMENT | User: {user_id}")
    await add_system_log(user_id, "SUCCESSFUL_PAYMENT_RECEIVED")

    await message.answer("✅ Оплата прошла успешно! Начинаем квиз...")

    # Логируем в БД и выдаем билет
    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    await issue_random_tickets(user_id, 1, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer("Начинаем квиз за iPhone 17 PRO 256 Гб....", reply_markup=get_start_quiz_keyboard())

    # Проверка лимита
    await check_and_trigger_closure(message.bot)
