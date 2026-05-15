from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import YOOKASSA_PROVIDER_TOKEN, TICKET_LIMIT, CHANNEL_ID, OWNER_ID, QUIZ_PRICE
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection, log_payment
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
import logging
import sys

router = Router()

# YOOKASSA TEST INTEGRATION: Команда /testpay для владельца
@router.message(Command("testpay"))
async def cmd_testpay(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    issued = await issue_random_tickets(user_id, 1, "base")
    if not issued:
        await message.answer("Извините, билеты закончились!")
        return
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)
    await message.answer("✅ (Тест) Оплата прошла успешно! Начинаем квиз...", reply_markup=get_start_quiz_keyboard())

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    if await is_collection_closed():
        await message.answer(
            "🎉 <b>Сбор билетов завершён досрочно!</b>\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🎁 <b>Участвуй в розыгрыше iPhone 17!</b>\n\n"
        "Оплати 99 ₽ и получи:\n"
        "✅ 1 гарантированный билет\n"
        "✅ Возможность получить до +3 бонусных билетов за квиз\n\n"
        "Готов начать?",
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "pay_99")
async def process_pay(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("Сбор билетов завершен!", show_alert=True)
        return

    # YOOKASSA TEST INTEGRATION: Диагностика
    logging.info(f"PAYMENT_START: User {callback.from_user.id}")
    await callback.answer() # Снимаем прелоадер с кнопки немедленно

    status_msg = await callback.message.answer("⏳ Формируем счёт...")

    if not YOOKASSA_PROVIDER_TOKEN or YOOKASSA_PROVIDER_TOKEN == "YOUR_YOOKASSA_TOKEN":
        logging.error("ERROR: YOOKASSA_PROVIDER_TOKEN is not set or invalid!")
        await status_msg.edit_text("❌ Ошибка конфигурации платежей. Обратитесь в поддержку.")
        return

    try:
        logging.info(f"Sending invoice with token: {YOOKASSA_PROVIDER_TOKEN[:5]}...")
        await callback.message.answer_invoice(
            title="Билет участия в розыгрыше",
            description=f"1 билет + доступ к квизу за {QUIZ_PRICE} RUB",
            provider_token=YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет", amount=QUIZ_PRICE * 100)],
            payload="ticket_purchase_v1",
            start_parameter="ticket",
            provider_data='{"test": true}'
        )
        await status_msg.delete()
        logging.info("PAYMENT_INVOICE_SENT_SUCCESS")
    except Exception as e:
        logging.error(f"ERROR send_invoice: {e}")
        print("ERROR send_invoice:", e, file=sys.stderr)
        await status_msg.edit_text(f"❌ Ошибка оплаты: {e}")

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # YOOKASSA TEST INTEGRATION
    logging.info(f"PRE_CHECKOUT: {pre_checkout_query.id} from {pre_checkout_query.from_user.id}")
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    logging.info(f"SUCCESSFUL_PAYMENT: {user_id}")

    # Убедимся, что пользователь есть в базе
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    # YOOKASSA TEST INTEGRATION
    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    issued = await issue_random_tickets(user_id, 1, "base")
    if not issued:
        await message.answer("✅ Оплата прошла успешно! Но билеты закончились. Свяжитесь с поддержкой.")
        return

    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer(
        "✅ Оплата прошла успешно! Начинаем квиз...",
        reply_markup=get_start_quiz_keyboard()
    )

    # Проверка лимита билетов
    total_tickets = await get_total_tickets_count()
    if total_tickets >= TICKET_LIMIT:
        if not await is_collection_closed():
            await close_collection()
            try:
                await message.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🔥 <b>СБОР БИЛЕТОВ ЗАВЕРШЁН!</b>\n\n"
                         "Мы достигли лимита в 2500 билетов раньше срока.\n"
                         "Спасибо всем, кто принял участие!\n\n"
                         "Дата и время прямого розыгрыша будет объявлена в ближайшие часы.",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Failed to send to channel: {e}")
