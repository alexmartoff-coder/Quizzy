from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.callback_query(F.data == "use_free_attempt")
async def start_free_attempt(callback: CallbackQuery):
    user_id = callback.from_user.id

    if await is_collection_closed():
        await callback.answer("🎉 Приём заявок завершён!", show_alert=True)
        return

    from database.db import has_user_used_free_attempt
    if await has_user_used_free_attempt(user_id):
        await callback.answer("Вы уже использовали свою бесплатную попытку.", show_alert=True)
        return

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await callback.message.answer(
            f"✅ Ваша заявка №{ticket_num:05d} создана.\n\nГотовы пройти квиз?",
            reply_markup=get_start_quiz_keyboard()
        )
        try: await callback.message.delete()
        except: pass
    else:
        await callback.answer("Ошибка при создании заявки.", show_alert=True)

@payment_router.callback_query(F.data == "pay_99_rub")
async def start_payment_callback(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("🎉 Приём заявок завершён!", show_alert=True)
        return

    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Поддержка конкурса + попытка",
            description="Дополнительная попытка в конкурсе iPhone 17 PRO 256 Гб.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Поддержка", amount=9900)],
            payload="ticket_purchase"
        )
        try: await callback.message.delete()
        except: pass
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")

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
        await message.answer(
            f"Ваша платная заявка №{ticket_num:05d} создана.\n\nГотовы пройти квиз?",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании платной заявки.")

    await check_and_trigger_closure(message.bot)
