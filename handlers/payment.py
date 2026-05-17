from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, add_system_log
from keyboards.menu import get_start_quiz_keyboard
import logging
import config

router = Router()

# 🧪 Тестовый режим ЮKassa

# --- ОБРАБОТЧИКИ ПЛАТЕЖЕЙ ---

@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Ответ на предварительный запрос (нужен в течение 10 секунд)."""
    user_id = pre_checkout_query.from_user.id
    logging.info(f"PAYMENT_STEP: PreCheckoutQuery received. ID: {pre_checkout_query.id}, User: {user_id}")
    await add_system_log(user_id, "PRE_CHECKOUT_RECEIVED", f"ID: {pre_checkout_query.id}")
    try:
        await pre_checkout_query.answer(ok=True)
        logging.info(f"PAYMENT_STEP: PreCheckoutQuery answered OK. User: {user_id}")
        await add_system_log(user_id, "PRE_CHECKOUT_OK")
    except Exception as e:
        logging.error(f"PAYMENT_STEP: Error answering PreCheckoutQuery. User: {user_id}, Error: {e}")
        await add_system_log(user_id, "PRE_CHECKOUT_ERROR", str(e))

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка подтвержденного платежа."""
    user_id = message.from_user.id
    logging.info(f"PAYMENT_STEP: Successful payment received. User: {user_id}")
    await add_system_log(user_id, "SUCCESSFUL_PAYMENT_RECEIVED")
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
    logging.info(f"PAYMENT_STEP: User {user_id} clicked 'Play Quiz' button")
    await add_system_log(user_id, "BUTTON_CLICK_PLAY")

    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    if await is_collection_closed():
        logging.info(f"PAYMENT_STEP: Participation rejected - collection closed. User: {user_id}")
        await add_system_log(user_id, "PLAY_REJECTED_CLOSED")
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 3500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 PRO 256 Гб. состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    logging.info(f"PAYMENT_STEP: Attempting to send invoice. User: {user_id}")
    await add_system_log(user_id, "INVOICE_REQUESTED")
    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        # Для надежности приводим токен к строке и добавляем start_parameter
        token = str(config.YOOKASSA_PROVIDER_TOKEN)
        token_prefix = token[:10] if token else "None"
        logging.info(f"PAYMENT_STEP: Calling answer_invoice. User: {user_id}, Token prefix: {token_prefix}")

        await message.answer_invoice(
            title="Билет участия в розыгрыше",
            description="1 билет + доступ к квизу за iPhone 17 PRO 256 Гб.",
            provider_token=token,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=9900)],
            payload="ticket_purchase",
            start_parameter="iphone17pro_quiz"
        )
        logging.info(f"PAYMENT_STEP: answer_invoice successful. User: {user_id}")
        await add_system_log(user_id, "INVOICE_SENT")
    except Exception as e:
        logging.error(f"PAYMENT_STEP: answer_invoice failed. User: {user_id}, Error: {e}")
        await add_system_log(user_id, "INVOICE_ERROR", str(e))
        await message.answer(f"❌ Ошибка при формировании счёта: {e}")

