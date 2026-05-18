from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, add_system_log
from keyboards.menu import get_start_quiz_keyboard
import logging
import config

router = Router()

# 🧪 Тестовый режим ЮKassa

# Проверка конфигурации при загрузке модуля
if not config.YOOKASSA_PROVIDER_TOKEN:
    logging.warning("⚠️ PAYMENT_CONFIG: YOOKASSA_PROVIDER_TOKEN is not set in config!")

# --- ОБРАБОТЧИКИ ПЛАТЕЖЕЙ ---

@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Ответ на предварительный запрос (нужен в течение 10 секунд)."""
    user_id = pre_checkout_query.from_user.id
    logging.info(f"💳 PRE_CHECKOUT_ENTRY: User {user_id}, Query ID: {pre_checkout_query.id}")
    await add_system_log(user_id, "PRE_CHECKOUT_RECEIVED", f"ID: {pre_checkout_query.id}")
    try:
        await pre_checkout_query.answer(ok=True)
        logging.info(f"✅ PRE_CHECKOUT_EXIT: User {user_id} - Answered OK")
        await add_system_log(user_id, "PRE_CHECKOUT_OK")
    except Exception as e:
        logging.error(f"❌ PRE_CHECKOUT_ERROR: User {user_id} - {e}", exc_info=True)
        await add_system_log(user_id, "PRE_CHECKOUT_ERROR", str(e))

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка подтвержденного платежа."""
    user_id = message.from_user.id
    logging.info(f"💰 SUCCESSFUL_PAYMENT_ENTRY: User {user_id}")
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

@router.message(Command("paystatus"))
async def cmd_paystatus(message: Message):
    if message.from_user.id != config.OWNER_ID: return
    token = config.YOOKASSA_PROVIDER_TOKEN
    if not token or token == "YOUR_YOOKASSA_TOKEN":
        await message.answer("❌ YOOKASSA_PROVIDER_TOKEN не установлен!")
    else:
        await message.answer(f"✅ Токен загружен. Префикс: {token[:10]}...")

@router.message(F.text == "🎁 Играть в квиз за iPhone 17 PRO 256 Гб.")
async def cmd_play(message: Message):
    user_id = message.from_user.id
    logging.info(f"DEBUG: User {user_id} triggered participation button")
    await add_system_log(user_id, "BUTTON_CLICK_PLAY")

    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    if await is_collection_closed():
        logging.info(f"INFO: Participation attempt rejected (collection closed) for user {user_id}")
        await add_system_log(user_id, "PLAY_REJECTED_CLOSED")
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 3500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 PRO 256 Гб. состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    payload = "ticket_purchase"
    logging.info(f"DEBUG: Preparing to send invoice. User ID: {user_id}, Payload: {payload}")
    await add_system_log(user_id, "INVOICE_REQUESTED")
    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        # Валидация конфигурации перед отправкой
        token = str(config.YOOKASSA_PROVIDER_TOKEN)
        if not token or token in ("None", "", "YOUR_YOOKASSA_TOKEN"):
            logging.warning(f"⚠️ YOOKASSA_PROVIDER_TOKEN is missing or invalid for user {user_id}")
            raise ValueError("Invalid YOOKASSA_PROVIDER_TOKEN")

        currency = "RUB"
        price_amount = 9900 # 99.00 RUB

        logging.info(f"DEBUG: Calling answer_invoice for user {user_id}. Token prefix: {token[:10]}...")

        msg = await message.answer_invoice(
            title="Билет участия в розыгрыше",
            description="1 билет + доступ к квизу за iPhone 17 PRO 256 Гб.",
            provider_token=token,
            currency=currency,
            prices=[LabeledPrice(label="Билет", amount=price_amount)],
            payload=payload,
            start_parameter="pay_ticket"
        )
        logging.info(f"INFO: Invoice sent successfully. Message ID: {msg.message_id} for user {user_id}")
        await add_system_log(user_id, "INVOICE_SENT")
    except Exception as e:
        logging.error(f"❌ Failed to send invoice to user {user_id}: {e}", exc_info=True)
        await add_system_log(user_id, "INVOICE_ERROR", str(e))
        await message.answer(f"❌ Ошибка при формировании счёта: {e}")

