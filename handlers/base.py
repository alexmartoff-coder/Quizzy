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
        kb, progress = await get_main_menu_keyboard(user_id)
        await message.answer(
            agreement_text,
            reply_markup=get_rules_agreement_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await message.answer(f"{progress}\n\nИспользуйте меню для навигации.", reply_markup=kb)
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"<b>Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!</b>\n\n"
        "Участвуйте в квизе, отвечайте на вопросы и получайте билеты на розыгрыш iPhone 17.\n"
        "Каждый платёж (99 ₽) даёт 1 гарантированный билет + до 3 бонусных за отличный результат!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "accept_rules")
async def accept_rules_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("✅ Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    await callback.message.answer(
        "<b>Спасибо! Теперь вы можете участвовать в конкурсе.</b>\n\n"
        "Участвуйте в квизе, отвечайте на вопросы и получайте билеты на розыгрыш iPhone 17.\n"
        "Каждый платёж (99 ₽) даёт 1 гарантированный билет + до 3 бонусных за отличный результат!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Приложение к правилам для конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "Интеллектуальный конкурс «iPhone 17 PRO 256 Гб»\n"
        "<b>Тематика квиза:</b> компания Apple, её устройства, операционные системы, технологии, история.\n"
        "<b>Приз:</b> iPhone 17 PRO 256 Гб (один экземпляр).\n"
        "<b>Количество платных билетов для завершения сбора:</b> 2500 (две тысячи пятьсот).\n"
        "<b>Окончание сбора:</b> автоматически при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "<b>Розыгрыш:</b> проводится с помощью генератора случайных чисел Random.org среди всех выданных билетов.\n\n"
        "Все остальные условия — в соответствии с Основными правилами интеллектуальных конкурсов, размещённых по ссылке:\n"
        "https://cbda.ru/rules/base\n\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100. (самозанятый).\n"
        "Участие в конкурсе означает полное согласие с правилами и условиями обработки данных."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз за iPhone 17» в меню!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            else:
                status_text = "✅ Получен"
                score_text = f"\nРезультат квиза: {score}/10"

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    # Проверка, завершен ли розыгрыш
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT ticket_number, user_id, score, total_time FROM final_results WHERE is_mini_quiz = (SELECT MAX(is_mini_quiz) FROM final_results) ORDER BY score DESC, total_time ASC LIMIT 1") as cursor:
            winner = await cursor.fetchone()
        async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as cursor:
            published = await cursor.fetchone()

    if winner and published:
        async with aiosqlite.connect("bot_database.db") as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
                u = await c.fetchone()
                username = "@" + u[0] if u[0] else u[1]

        minutes = int(winner[3] // 60)
        seconds = int(winner[3] % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        text = (
            "🏆 <b>Победитель конкурса определён!</b>\n\n"
            f"Победитель: {username} (заявка №{winner[0]:05d})\n"
            f"Результат: {winner[2]}/8, время {time_str}\n"
            "Приз: iPhone 17 PRO 256 Гб"
        )
        await message.answer(text, parse_mode="HTML")
        return

    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд финалистов пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, total_tickets) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{total_tickets}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    # Проверка, завершен ли розыгрыш
    async with aiosqlite.connect("bot_database.db") as db:
        async with db.execute("SELECT ticket_number, user_id, score, total_time FROM final_results WHERE is_mini_quiz = (SELECT MAX(is_mini_quiz) FROM final_results) ORDER BY score DESC, total_time ASC LIMIT 1") as cursor:
            winner = await cursor.fetchone()
        async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as cursor:
            published = await cursor.fetchone()

    if winner and published:
        async with aiosqlite.connect("bot_database.db") as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
                u = await c.fetchone()
                username = "@" + u[0] if u[0] else u[1]

        minutes = int(winner[3] // 60)
        seconds = int(winner[3] % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        text = (
            "🏆 <b>Победитель конкурса определён!</b>\n\n"
            f"Победитель: {username} (заявка №{winner[0]:05d})\n"
            f"Результат: {winner[2]}/8, время {time_str}\n"
            "Приз: iPhone 17 PRO 256 Гб\n\n"
            "Поздравляем победителя!\n"
            "<b>ЖДЁМ ВАС НА НОВЫХ КОНКУРСАХ!</b>\n"
            "Следите за стартом в нашем канале @quizzy_best"
        )
        await message.answer(text, parse_mode="HTML")
        return

    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
