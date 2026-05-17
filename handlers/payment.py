from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import logging
import config

router = Router()

# 🧪 Тестовый режим ЮKassa

# --- ОБРАБОТЧИКИ ПЛАТЕЖЕЙ ---

@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Ответ на предварительный запрос (нужен в течение 10 секунд)."""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка подтвержденного платежа."""
    user_id = message.from_user.id
    await message.answer("✅ Оплата прошла успешно!")

    # Гарантируем регистрацию
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    # Логируем в БД
    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    # Выдаем билет и готовим квиз
    await issue_random_tickets(user_id, 1, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer("Начинаем квиз за iPhone 17 PRO 256 Гб....", reply_markup=get_start_quiz_keyboard())

    # Проверка лимита после выдачи билета
    await check_and_trigger_closure(message.bot)

# --- ГЛАВНЫЕ КОМАНДЫ ---

@router.message(F.text == "🎁 Играть в квиз за iPhone 17 PRO 256 Гб.")
async def cmd_play(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 3500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 PRO 256 Гб. состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    await message.answer("🧾 Формируем счёт на 99 RUB...")

    await message.answer_invoice(
        title="Билет участия в розыгрыше",
        description="1 билет + доступ к квизу за iPhone 17 PRO 256 Гб.",
        provider_token=config.YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Билет", amount=9900)],
        payload="ticket_purchase"
    )

