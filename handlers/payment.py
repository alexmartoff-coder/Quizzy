from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from aiogram.filters import Command
from config import QUIZ_PRICE, PAYMENT_PROVIDER_TOKEN, TICKET_LIMIT, BOT_TOKEN, CHANNEL_ID, OWNER_ID
from database.db import increment_ticket_id, add_ticket, set_quiz_session, is_collection_closed, get_total_tickets_count, close_collection
from keyboards.menu import get_payment_keyboard, get_start_quiz_keyboard
from datetime import datetime
from aiogram import Bot
import logging
import html

router = Router()

async def simulate_successful_payment(message: Message, user_id: int):
    start_ticket_id = await increment_ticket_id(1)
    await add_ticket(user_id, start_ticket_id, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.bot.send_message(
        chat_id=user_id,
        text=f"<b>(Тестовый режим)</b> ✅ Оплата прошла! Твой базовый билет <b>№{start_ticket_id:04d}</b> получен.\n\n"
             "Теперь давай проверим твои знания и попробуем заработать бонусные билетов!",
        reply_markup=get_start_quiz_keyboard(),
        parse_mode="HTML"
    )

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

@router.message(Command("testpay"))
async def cmd_testpay(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await simulate_successful_payment(message, message.from_user.id)

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    if await is_collection_closed():
        await message.answer(
            "🎉 <b>Сбор билетов завершён досрочно!</b>\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!",
            parse_mode="HTML"
        )
        return

    prefix = "<b>(Тестовый режим)</b> "

    await message.answer(
        f"{prefix}🎁 <b>Участвуй в розыгрыше iPhone 17!</b>\n\n"
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

    await simulate_successful_payment(callback.message, callback.from_user.id)
    await callback.answer()
    return

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    start_ticket_id = await increment_ticket_id(1)
    user_id = message.from_user.id
    await add_ticket(user_id, start_ticket_id, "base")
    await set_quiz_session(user_id, score=0, current_question=0, is_active=True)

    await message.answer(
        f"✅ Оплата прошла! Твой базовый билет <b>№{start_ticket_id:04d}</b> получен.\n\n"
        "Теперь давай проверим твои знания и попробуем заработать бонусные билеты!",
        reply_markup=get_start_quiz_keyboard(),
        parse_mode="HTML"
    )

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
