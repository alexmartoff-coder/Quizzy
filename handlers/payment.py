from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import QUIZ_PRICE, PAYMENT_PROVIDER_TOKEN, TICKET_LIMIT, BOT_TOKEN, CHANNEL_ID, OWNER_ID
from database.db import increment_ticket_id, add_ticket, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
from datetime import datetime
from aiogram import Bot
import logging

router = Router()

# ТЕСТОВЫЙ РЕЖИМ: Имитация успешной оплаты
# Убрать после теста
async def simulate_successful_payment(message: Message, user_id: int):
    # Issue base ticket
    start_ticket_id = await increment_ticket_id(1)
    await add_ticket(user_id, start_ticket_id, "base")

    # Start quiz session
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.bot.send_message(
        chat_id=user_id,
        text=f"(Тестовый режим) ✅ Оплата прошла! Твой базовый билет №{start_ticket_id} получен.\n\n"
             "Теперь давай проверим твои знания и попробуем заработать бонусные билеты!",
        reply_markup=get_start_quiz_keyboard()
    )

    # Check if we hit the limit
    total_tickets = await get_total_tickets_count()
    if total_tickets >= TICKET_LIMIT:
        if not await is_collection_closed():
            await close_collection()
            try:
                await message.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                         "Мы достигли лимита в 2500 билетов раньше срока.\n"
                         "Спасибо всем, кто принял участие!\n\n"
                         "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
                )
            except Exception as e:
                logging.error(f"Failed to send to channel: {e}")

# ТЕСТОВЫЙ РЕЖИМ: Команда /testpay для владельца
# Убрать после теста
@router.message(Command("testpay"))
async def cmd_testpay(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await simulate_successful_payment(message, message.from_user.id)

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    # ТЕСТОВЫЙ РЕЖИМ: Пометка сообщения
    # Убрать после теста
    prefix = "(Тестовый режим) "

    await message.answer(
        f"{prefix}🎁 **Участвуй в розыгрыше iPhone 17!**\n\n"
        "Оплати 99 ₽ и получи:\n"
        "✅ 1 гарантированный билет\n"
        "✅ Возможность получить до +3 бонусных билетов за квиз\n\n"
        "Готов начать?",
        reply_markup=get_payment_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "pay_99")
async def process_pay(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("Сбор билетов завершен!", show_alert=True)
        return

    # ТЕСТОВЫЙ РЕЖИМ: Имитация вместо инвойса
    # Убрать после теста
    await simulate_successful_payment(callback.message, callback.from_user.id)
    await callback.answer()
    return

    # Настоящая оплата (пропускается в тестовом режиме)
    await callback.message.answer_invoice(
        title="Участие в квизе за iPhone 17",
        description="Оплата 1 базового билета + доступ к квизу",
        payload="quiz_payment",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Билет + Квиз", amount=QUIZ_PRICE * 100)], # In kopeks
        start_parameter="quiz_iphone_17"
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    # Issue base ticket
    start_ticket_id = await increment_ticket_id(1)
    user_id = message.from_user.id
    await add_ticket(user_id, start_ticket_id, "base")

    # Start quiz session
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer(
        f"✅ Оплата прошла! Твой базовый билет №{start_ticket_id} получен.\n\n"
        "Теперь давай проверим твои знания и попробуем заработать бонусные билеты!",
        reply_markup=get_start_quiz_keyboard()
    )

    # Check if we hit the limit
    total_tickets = await get_total_tickets_count()
    if total_tickets >= TICKET_LIMIT:
        if not await is_collection_closed():
            await close_collection()
            # Send to channel using the bot instance from the message
            try:
                await message.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                         "Мы достигли лимита в 2500 билетов раньше срока.\n"
                         "Спасибо всем, кто принял участие!\n\n"
                         "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
                )
            except Exception as e:
                logging.error(f"Failed to send to channel: {e}")
