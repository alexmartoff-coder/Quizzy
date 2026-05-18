from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, add_system_log
from keyboards.menu import get_start_quiz_keyboard
import logging
import config

payment_router = Router()

# 🧪 Тестовый режим ЮKassa

# Проверка конфигурации при загрузке модуля
if not config.YOOKASSA_PROVIDER_TOKEN:
    logging.warning("⚠️ PAYMENT_CONFIG: YOOKASSA_PROVIDER_TOKEN is not set in config!")

# --- ОБРАБОТЧИКИ ПЛАТЕЖЕЙ ---

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Ответ на предварительный запрос (нужен в течение 10 секунд)."""
    user_id = pre_checkout_query.from_user.id
    print(f"✅ PRE_CHECKOUT_QUERY RECEIVED | User: {user_id}")
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.successful_payment)
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

@payment_router.message(Command("paystatus"))
async def cmd_paystatus(message: Message):
    if message.from_user.id != config.OWNER_ID: return
    token = config.YOOKASSA_PROVIDER_TOKEN
    if not token or token == "YOUR_YOOKASSA_TOKEN":
        await message.answer("❌ YOOKASSA_PROVIDER_TOKEN не установлен!")
    else:
        await message.answer(f"✅ Токен загружен. Префикс: {token[:10]}...")

@payment_router.message(F.text == "🎁 Играть в квиз за iPhone 17 PRO 256 Гб.")
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
    print(f"⏳ INVOICE_PREPARING | User: {user_id}")
    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        token = str(config.YOOKASSA_PROVIDER_TOKEN)

        msg = await message.answer_invoice(
            title="Билет участия в розыгрыше",
            description="1 билет + доступ к квизу за iPhone 17 PRO 256 Гб.",
            provider_token=token,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=9900)],
            payload="ticket_purchase",
            start_parameter="pay_ticket"
        )
        print(f"🚀 INVOICE_SENT | Message ID: {msg.message_id} | User: {user_id}")
    except Exception as e:
        print(f"❌ INVOICE_ERROR | User: {user_id} | Error: {e}")
        await message.answer(f"❌ Ошибка при формировании счёта: {e}")

