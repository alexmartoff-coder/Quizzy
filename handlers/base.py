from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure, get_paid_tickets_count, has_user_used_free_attempt, get_user_applications
from keyboards.menu import get_main_menu_keyboard
import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"{progress}\n\n"
        "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!\n\n"
        "Каждый участник получает 1 бесплатную заявку на участие.\n"
        "Вы также можете поддержать конкурс и получить дополнительную попытку (99 ₽).",
        reply_markup=kb
    )

@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила интеллектуального конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "<b>1. Отборочный этап</b>\n"
        "1.1. Отборочный этап заканчивается при достижении количества платных заявок, равного 3500. Бесплатные заявки не влияют на завершение этапа.\n"
        "1.2. Каждый участник может подать одну бесплатную заявку и неограниченное количество платных (Поддержка конкурса + дополнительная попытка (99 ₽)).\n"
        "1.3. <b>Бесплатная заявка</b> — участник проходит квиз из 10 вопросов. Для выхода в финал необходимо дать <b>9 или 10</b> правильных ответов.\n"
        "1.4. <b>Платная заявка</b> — участник, внесший добровольную поддержку (99 руб.), получает дополнительную попытку. Для выхода в финал достаточно <b>8, 9 или 10</b> правильных ответов.\n"
        "1.5. Если участник набирает меньше проходного балла (менее 9 для бесплатной, менее 8 для платной), заявка не становится финалистской.\n\n"
        "<b>2. Финал</b>\n"
        "Победитель будет определен среди финалистских заявок через генератор случайных чисел random.org.\n\n"
        "Прямой эфир состоится в канале @mozgo_boy."
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
            status_text = "⏳ Ожидает квиза" if status == "pending" else ("✅ Прошла в Финал" if status == "finalist" else "❌ Не прошла")
            score_text = f" ({score}/10)" if score is not None else ""
            text += f"🎫 №{t_num:05d} — {status_text}{score_text}\n"
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
    await message.answer("По всем вопросам обращайтесь: sasha@cbca.ru")
