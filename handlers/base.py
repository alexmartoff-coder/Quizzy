from database.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    has_user_used_free_attempt, get_user_applications,
    has_accepted_rules, mark_rules_accepted
)
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard, get_participation_keyboard
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

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play_quiz(message: Message):
    user_id = message.from_user.id
    if await is_collection_closed():
        await message.answer("🎉 Приём заявок завершён!")
        return

    warning_text = (
        "⚠️ <b>Внимание!</b>\n\n"
        "Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет "
        "и входящие звонки не мешали прохождению квиза.\n\n"
        "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш."
    )

    used_free = await has_user_used_free_attempt(user_id)
    await message.answer(
        warning_text,
        reply_markup=get_participation_keyboard(not used_free),
        parse_mode="HTML"
    )

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "1. <b>Общие положения:</b> Интеллектуальный конкурс проводится с целью популяризации знаний о технологиях Apple.\n"
        "2. <b>Приз:</b> iPhone 17 PRO 256 Гб.\n"
        "3. <b>Участие:</b>\n"
        "   - 1 бесплатная попытка для каждого пользователя.\n"
        "   - Платные попытки: 99 ₽ за каждую.\n"
        "4. <b>Механика билетов:</b>\n"
        "   - Каждая попытка (прохождение квиза) дает 1 базовый билет.\n"
        "   - Бонусные билеты за результат:\n"
        "     ✅ 10/10 — +3 билета\n"
        "     ✅ 9/10 — +2 билета\n"
        "     ✅ 8/10 — +1 билет\n"
        "5. <b>Сроки:</b>\n"
        "   - Сбор заявок до 10 апреля 2026 г. или до достижения 2500 платных заявок.\n"
        "6. <b>Определение победителя:</b>\n"
        "   - Победитель выбирается случайным образом среди всех выданных билетов с помощью random.org.\n"
        "   - Розыгрыш проводится в прямом эфире в канале @mozgo_boy.\n\n"
        "Полные правила: <a href='https://cbda.ru/rules/base'>cbda.ru/rules/base</a>"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть» в меню!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            else:
                status_text = "✅ Участвует в розыгрыше"
                score_text = f"\nРезультат квиза: {score}/10"

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n\n"

        text += "<i>Бонусные билеты суммируются с основными.</i>"
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
    await message.answer("По всем вопросам обращайтесь в поддержку @mozgo_boy_admin или на почту alexandr@cbda.ru")
