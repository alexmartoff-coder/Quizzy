from database.db import add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure, get_user_applications
from keyboards.menu import get_main_menu_keyboard
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
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
        "Добро пожаловать в интеллектуальный квиз «iPhone 17 PRO 256 Гб»!\n\n"
        "Каждый платёж (99 ₽) даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе.",
        reply_markup=kb
    )

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "1. Участие стоит 99 ₽.\n"
        "2. За каждый платёж вы получаете 1 базовый билет.\n"
        "3. После оплаты вы проходите квиз из 10 вопросов (30 сек на каждый).\n"
        "4. Бонусные билеты за результат:\n"
        "   — 10 верных: +3 билета\n"
        "   — 9 верных: +2 билета\n"
        "   — 8 верных: +1 билет\n"
        "5. Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "6. Победитель будет выбран честно с помощью https://www.random.org/ среди всех выданных билетов.\n\n"
        "Следите за результатами в канале @mozgo_boy!"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз», чтобы участвовать!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        ticket_nums = [f"№{t_num:05d}" for t_num, status, score in apps]
        text += ", ".join(ticket_nums)
        text += f"\n\nВсего билетов: <b>{len(ticket_nums)}</b>"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard_handler(message: Message):
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
