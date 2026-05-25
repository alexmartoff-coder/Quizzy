from database.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    has_user_used_free_attempt, get_user_applications, issue_ticket, set_quiz_session,
    has_accepted_rules, mark_rules_accepted
)
from keyboards.menu import get_main_menu_keyboard, get_start_quiz_keyboard, get_rules_agreement_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    if not await has_accepted_rules(user_id):
        agreement_text = (
            "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами конкурса</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты) в целях проведения конкурса. "
            "Данные не являются персональными по 152-ФЗ»."
        )
        await message.answer(
            agreement_text,
            reply_markup=get_rules_agreement_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"{progress}\n\n"
        "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!",
        reply_markup=kb
    )

@router.callback_query(F.data == "accept_rules")
async def accept_rules_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("✅ Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    await callback.message.answer(
        f"{progress}\n\n"
        "Спасибо! Теперь вы можете участвовать в конкурсе.\n\n"
        "Каждый участник получает 1 бесплатную заявку на участие.\n"
        "Вы также можете поддержать конкурс и получить дополнительную попытку (99 ₽).",
        reply_markup=kb
    )
    try:
        await callback.message.delete()
    except:
        pass


@router.message(F.text == "🏆 Войти в Финал")
async def cmd_enter_final(message: Message):
    user_id = message.from_user.id
    from database.db_final import is_final_registration_open, has_user_registered_for_final, get_user_finalist_tickets, register_for_final
    import aiosqlite

    if not await is_final_registration_open():
        await message.answer("Регистрация в Финал сейчас закрыта.")
        return

    if await has_user_registered_for_final(user_id):
        await message.answer("Вы уже вошли в Финал.")
        return

    tickets = await get_user_finalist_tickets(user_id)
    if not tickets:
        await message.answer("У вас нет финалистских заявок.")
        return

    await register_for_final(user_id)

    # Инициализация сессии финала
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("INSERT OR REPLACE INTO final_sessions (user_id, current_ticket_index, is_active) VALUES (?, 0, 1)", (user_id,))
        await db.commit()

    await message.answer(
        f"✅ Вы успешно вошли в Финал!\n"
        f"Всего ваших заявок: {len(tickets)}\n\n"
        f"Квиз для первой заявки №{tickets[0]:05d} начнется через мгновение..."
    )

    # Запуск первого квиза
    from handlers.final_quiz import start_final_quiz_for_ticket
    await start_final_quiz_for_ticket(message.bot, user_id, tickets[0])

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "Интеллектуальный конкурс «iPhone 17 PRO 256 Гб»\n"
        "<b>Тематика квиза:</b> компания Apple, её устройства, операционные системы, технологии, история.\n"
        "<b>Приз:</b> iPhone 17 PRO 256 Гб (один экземпляр).\n"
        "<b>Дата проведения:</b> до 10 апреля 2026 г.\n\n"
        "Все условия конкурса — в соответствии с Основными правилами интеллектуальных конкурсов, размещённых по ссылке:\n"
        "https://cbda.ru/rules/base\n\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100 (самозанятый).\n"
        "Участие в конкурсе означает полное согласие с правилами и условиями обработки данных."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз», чтобы участвовать!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            else:
                status_text = f"— Результат: {score}/10"
                score_text = ""

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")
