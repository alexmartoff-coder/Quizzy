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
        "Пройди квиз и выиграй iPhone 17!",
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
        "Пройди квиз и выиграй iPhone 17!",
        reply_markup=kb
    )
    try:
        await callback.message.delete()
    except:
        pass


@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила розыгрыша «iPhone 17 PRO 256 Гб»</b>\n\n"
        "1. <b>Приз:</b> iPhone 17 PRO 256 Гб.\n"
        "2. <b>Как участвовать:</b> Нажмите «🎁 Играть», оплатите 99 ₽. Вы получите 1 базовый билет и доступ к квизу.\n"
        "3. <b>Бонусы:</b> За правильные ответы в квизе (10 вопросов, по 30 сек) начисляются бонусные билеты:\n"
        "   — 10 верных: +3 билета\n"
        "   — 9 верных: +2 билета\n"
        "   — 8 верных: +1 билет\n"
        "4. <b>Лимиты:</b> Сбор билетов завершается при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "5. <b>Розыгрыш:</b> Победитель будет выбран случайным образом через Random.org среди всех выданных номеров билетов.\n\n"
        "Подробные правила: https://cbda.ru/rules/base\n"
        "Организатор: ИНН 470102947100"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы участвовать!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            else:
                status_text = "✅ Участвует в розыгрыше"
                score_text = f" (Квиз: {score}/10)"

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📊 Лидерборд")
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

@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")
