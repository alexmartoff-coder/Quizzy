from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import YOOKASSA_PROVIDER_TOKEN, TICKET_LIMIT, CHANNEL_ID, OWNER_ID
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection, log_payment
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
import logging

router = Router()

# 1. ОБЯЗАТЕЛЬНЫЙ ОБРАБОТЧИК pre_checkout_query
# Должен быть зарегистрирован и отвечать True, иначе форма оплаты не откроется
@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    print(f"PRE_CHECKOUT_QUERY from user {pre_checkout_query.from_user.id}")
    logging.info(f"PRE_CHECKOUT_QUERY received from {pre_checkout_query.from_user.id}")
    await pre_checkout_query.answer(ok=True)

# 2. ОБРАБОТЧИК successful_payment
# Срабатывает после подтверждения транзакции банком
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    print(f"SUCCESSFUL_PAYMENT from user {message.from_user.id}")
    logging.info(f"SUCCESSFUL_PAYMENT confirmed for {message.from_user.id}")

    await message.answer("✅ Оплата прошла успешно!")

    user_id = message.from_user.id
    # Регистрация
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    # Логирование
    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    # Билет
    await issue_random_tickets(user_id, 1, "base")
    # Квиз
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer("Начинаем квиз за iPhone 17...", reply_markup=get_start_quiz_keyboard())

# --- Основные хендлеры ---

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён досрочно!")
        return
    await message.answer(
        "🎁 <b>Участвуй в розыгрыше iPhone 17!</b>\n\nОплати 99 ₽ и получи доступ к квизу.",
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "pay_99")
async def process_pay(callback: CallbackQuery):
    # Убираем прелоадер с инлайн-кнопки
    await callback.answer()

    # Сообщение перед инвойсом
    await callback.message.answer("🧾 Формируем счёт...")

    try:
        # 3. Используем message.answer_invoice как просил юзер
        # Это отправит сообщение-счет в тот же чат
        await callback.message.answer_invoice(
            title="Билет участия в розыгрыше",
            description="1 билет + доступ к квизу",
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=9900)],
            payload="ticket_v1"
        )
        print("Invoice sent successfully")
    except Exception as e:
        print(f"ERROR sending invoice: {e}")
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")

@router.message(Command("testpay"))
async def cmd_testpay(message: Message):
    if message.from_user.id != OWNER_ID: return
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await issue_random_tickets(user_id, 1, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)
    await message.answer("✅ (Тест) Оплата прошла успешно! Начинаем квиз...", reply_markup=get_start_quiz_keyboard())
