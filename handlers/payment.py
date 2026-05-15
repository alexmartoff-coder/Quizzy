from aiogram import Router, F, Bot
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import YOOKASSA_PROVIDER_TOKEN, TICKET_LIMIT, CHANNEL_ID, OWNER_ID
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection, log_payment
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
import logging

router = Router()

# --- ОБРАБОТЧИКИ ПЛАТЕЖЕЙ (YOOKASSA TEST INTEGRATION) ---

@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Ответ на предварительный запрос (нужен в течение 10 секунд)."""
    logging.info(f"PRE_CHECKOUT_QUERY: {pre_checkout_query.id}")
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка подтвержденного платежа."""
    logging.info(f"SUCCESSFUL_PAYMENT: {message.from_user.id}")

    await message.answer("✅ Оплата прошла успешно!")

    user_id = message.from_user.id
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

    await message.answer("Начинаем квиз за iPhone 17...", reply_markup=get_start_quiz_keyboard())

# --- ГЛАВНЫЕ КОМАНДЫ ---

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён досрочно!")
        return

    await message.answer(
        "🎁 <b>Участвуй в розыгрыше iPhone 17!</b>\n\n"
        "Оплати 99 ₽ и получи:\n"
        "✅ 1 гарантированный билет\n"
        "✅ Возможность получить бонусные билеты за квиз\n\n"
        "Готов начать?",
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "pay_99")
async def process_pay(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("Сбор билетов завершен!", show_alert=True)
        return

    # 1. Немедленно снимаем прелоадер с кнопки
    await callback.answer()

    # 2. Обратная связь пользователю
    await callback.message.answer("🧾 Формируем счёт на оплату...")

    logging.info(f"PAYMENT: Sending invoice to {callback.from_user.id}")

    try:
        # 3. Отправка инвойса (МИНИМАЛЬНЫЙ НАБОР ПАРАМЕТРОВ)
        # Если форма не появляется, проверьте YOOKASSA_PROVIDER_TOKEN в .env
        await callback.message.answer_invoice(
            title="Билет на участие в розыгрыше",
            description="1 билет + доступ к квизу",
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=9900)],
            payload="ticket_v1"
        )
        logging.info("PAYMENT: Invoice sent successfully")
    except Exception as e:
        logging.error(f"PAYMENT: Error sending invoice: {e}")
        await callback.message.answer(f"❌ Ошибка при создании счета: {e}")

@router.message(Command("testpay"))
async def cmd_testpay(message: Message):
    if message.from_user.id != OWNER_ID: return
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await issue_random_tickets(user_id, 1, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)
    await message.answer("✅ (Тест) Оплата прошла успешно! Начинаем квиз...", reply_markup=get_start_quiz_keyboard())
