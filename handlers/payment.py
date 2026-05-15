from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import QUIZ_PRICE, YOOKASSA_PROVIDER_TOKEN, TICKET_LIMIT, BOT_TOKEN, CHANNEL_ID, OWNER_ID
from database.db import add_user, issue_random_tickets, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection, log_payment
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
from datetime import datetime
from aiogram import Bot
import logging
import html

router = Router()

# YOOKASSA TEST INTEGRATION: Команда /testpay для владельца (эмуляция успешной оплаты)
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
    # Убедимся, что пользователь есть в базе
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

    # YOOKASSA TEST INTEGRATION
    await callback.message.answer_invoice(
        title="Билет на участие в розыгрыше",
        description="1 билет + доступ к квизу (99 RUB)",
        payload="ticket_purchase",
        provider_token=YOOKASSA_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Билет", amount=9900)],
        start_parameter="iphone17_quiz",
        is_flexible=False
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # YOOKASSA TEST INTEGRATION
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    # Убедимся, что пользователь есть в базе
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    # YOOKASSA TEST INTEGRATION: Логирование платежа
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
        await message.answer("Извините, билеты закончились!")
        return

    ticket_num = issued[0]
    # Установка сессии квиза
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer(
        "✅ Оплата прошла успешно! Начинаем квиз...",
        reply_markup=get_start_quiz_keyboard(),
        parse_mode="HTML"
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
