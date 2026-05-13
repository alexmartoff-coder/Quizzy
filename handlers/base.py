from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, get_user_tickets, get_leaderboard, is_collection_closed
from keyboards.menu import get_main_menu_keyboard
from datetime import datetime
from config import DEADLINE_DATE

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(
        "Добро пожаловать в квиз @prekrasenday_bot!\n\n"
        "Участвуй в розыгрыше iPhone 17. Один билет стоит 99 ₽. "
        "За хороший результат в квизе можно получить до +3 бонусных билетов!",
        reply_markup=await get_main_menu_keyboard()
    )

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    await message.answer(
        "📜 **Правила розыгрыша**\n\n"
        "1. Стоимость участия — 99 ₽.\n"
        "2. За каждую оплату вы получаете 1 гарантированный базовый билет.\n"
        "3. После оплаты начинается квиз из 10 вопросов.\n"
        "4. Бонусные билеты:\n"
        "   - 10 правильных ответов: +3 билета\n"
        "   - 9 правильных ответов: +2 билета\n"
        "   - 8 правильных ответов: +1 билет\n"
        "5. Сбор билетов завершается при достижении 2500 билетов или 10 апреля 2026 года.\n"
        "6. Победитель будет выбран с помощью random.org в прямом эфире @mozgo_boy.",
        parse_mode="Markdown"
    )

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    tickets = await get_user_tickets(message.from_user.id)
    if not tickets:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы участвовать!")
    else:
        tickets_str = ", ".join(map(str, tickets))
        await message.answer(f"Твои билеты ({len(tickets)} шт.):\n{tickets_str}")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard()
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 **Топ участников по количеству билетов:**\n\n"
    for i, (username, full_name, count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — {count} бил.\n"

    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь к @mozgo_boy_admin")
