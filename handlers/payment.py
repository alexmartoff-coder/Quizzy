from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_play_flow(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён досрочно!\n\nМы набрали 2500+ билетов. Спасибо всем участникам!\n\nРозыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\nСледи за обновлениями!")
        return

    from database.db import has_user_used_free_attempt
    used_free = await has_user_used_free_attempt(user_id)

    description = (
        "<b>🎁 Розыгрыш iPhone 17</b>\n\n"
        "Правила просты:\n"
        "1. Каждый платёж 99 ₽ даёт 1 базовый билет.\n"
        "2. Пройди квиз из 10 вопросов и получи до +3 бонусных билетов:\n"
        "   ✅ 10/10 — +3 билета\n"
        "   ✅ 9/10 — +2 билета\n"
        "   ✅ 8/10 — +1 билет\n\n"
        "Твои шансы на победу растут с каждым билетом!"
    )

    if not used_free:
        description += "\n\n🎁 <b>У тебя есть 1 БЕСПЛАТНАЯ попытка!</b>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆓 Использовать бесплатно", callback_data="use_free")]
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 99 ₽", callback_data="pay_99")]
        ])

    await message.answer(description, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "use_free")
async def use_free_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    from database.db import has_user_used_free_attempt
    if await has_user_used_free_attempt(user_id):
        await callback.answer("Вы уже использовали бесплатную попытку!", show_alert=True)
        return

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз и получить бонусные билеты?"
        )
        await callback.message.edit_text(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await callback.message.answer("Ошибка при создании заявки.")
    await callback.answer()

@payment_router.callback_query(F.data == "pay_99")
async def pay_99_callback(callback: CallbackQuery):
    await callback.answer()
    await start_payment(callback.message, callback.from_user.id)

@payment_router.message(F.text == "💰 Поддержать (99 ₽)")
async def start_payment_msg(message: Message):
    await start_payment(message, message.from_user.id)

async def start_payment(message: Message, user_id: int):
    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён досрочно!\n\nМы набрали 2500+ билетов. Спасибо всем участникам!\n\nРозыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.")
        return

    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await message.bot.send_invoice(
            chat_id=user_id,
            title="Поддержка розыгрыша + попытка",
            description="Дополнительная попытка в розыгрыше iPhone 17.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Поддержка", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await message.answer(f"❌ Ошибка: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    user = message.from_user

    await add_user(user_id, user.username, user.full_name)
    await message.answer("✅ Оплата прошла успешно!")

    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    ticket_num = await issue_ticket(user_id, "paid")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз и получить бонусные билеты?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании платной заявки.")

    await check_and_trigger_closure(message.bot)
