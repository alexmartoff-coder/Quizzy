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
        "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!\n\n"
        "Каждый участник получает 1 бесплатную заявку на участие.\n"
        "Вы также можете поддержать конкурс и получить дополнительную попытку (99 ₽).",
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


@router.message(F.text == "🔥 Начать мини-квиз")
async def cmd_start_mini_quiz(message: Message):
    user_id = message.from_user.id
    from database.db_winner import get_user_mini_quiz_tickets
    tickets = await get_user_mini_quiz_tickets(user_id)
    if not tickets:
        await message.answer("У вас нет заявок для мини-квиза.")
        return

    await message.answer(f"🚀 Начинаем мини-квиз для {len(tickets)} заявок!")
    from handlers.final_quiz import start_final_quiz_for_ticket
    from utils.state_helper import get_state
    state = await get_state(message.bot, user_id)
    await start_final_quiz_for_ticket(message.bot, user_id, tickets[0], q_count=5, is_mini=True, state=state)

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
        "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
        "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
        f"Квиз для первой заявки №{tickets[0]:05d} начнется через мгновение...",
        parse_mode="HTML"
    )

    # Запуск первого квиза
    from handlers.final_quiz import start_final_quiz_for_ticket
    from utils.state_helper import get_state
    state = await get_state(message.bot, user_id)
    await start_final_quiz_for_ticket(message.bot, user_id, tickets[0], state=state)

@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Приложение к правилам для конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "Интеллектуальный конкурс «iPhone 17 PRO 256 Гб»\n"
        "<b>Тематика квиза:</b> компания Apple, её устройства, операционные системы, технологии, история.\n"
        "<b>Приз:</b> iPhone 17 PRO 256 Гб (один экземпляр).\n"
        "<b>Количество платных заявок для завершения Отборочного Этапа:</b> 3500 (три тысячи пятьсот). Бесплатные заявки не влияют на окончание приёма.\n"
        "<b>Старт Отборочного этапа:</b> 29 мая 2026 г. в 12:00 МСК.\n"
        "<b>Окончание Отборочного Этапа:</b> автоматически при достижении 3500 платных заявок.\n"
        "<b>Финал:</b> следующий календарный день после завершения Отборочного этапа в 19:00 по московскому времени.\n\n"
        "Все остальные условия — в соответствии с Основными правилами интеллектуальных конкурсов, размещённых по ссылке:\n"
        "https://cbda.ru/rules/base\n\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100. (самозанятый).\n"
        "Участие в конкурсе означает полное согласие с правилами и условиями обработки данных."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет заявок. Используй бесплатную попытку в меню!")
    else:
        text = "<b>Твои заявки:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            elif status == "finalist":
                status_text = "— прошла в Финал!"
                score_text = f"\nРезультат: {score}/10"
            else:
                status_text = "— Не прошла в финал"
                score_text = f"\nРезультат: {score}/10"

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📊 Лидерборд")
@router.message(F.text == "📊 Лидерборд финалистов")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд финалистов пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству финалистских заявок:</b>\n\n"
    for i, (username, full_name, finalist_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{finalist_count}</b> фин. заявок\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")
