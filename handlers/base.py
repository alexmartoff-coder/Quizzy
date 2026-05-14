from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, get_user_tickets, get_leaderboard, is_collection_closed
from keyboards.menu import get_main_menu_keyboard

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
    rules_text = (
        "📜 **Правила розыгрыша iPhone 17**\n\n"
        "Участие — платное. Стоимость одной попытки — **99 ₽**.\n\n"
        "За каждую оплату вы получаете:\n\n"
        "✅ 1 гарантированный билет\n\n"
        "🎁 до **+3 бонусных билетов** в зависимости от результата квиза:\n\n"
        "10/10 правильных → +3 билета\n"
        "9/10 → +2 билета\n"
        "8/10 → +1 билет\n"
        "менее 8 → бонусов нет\n\n"
        "**Все билеты** (базовые + бонусные) участвуют в розыгрыше.\n\n"
        "**Сбор билетов** автоматически прекращается, как только набрано **2500 билетов**.\n\n"
        "После остановки сбора:\n"
        "❌ играть и оплачивать нельзя\n"
        "✅ можно посмотреть свои билеты, лидерборд и правила\n\n"
        "**Розыгрыш** проводится честно через генератор случайных чисел **random.org**.\n\n"
        "**Прямой эфир** с определением победителя состоится в канале **@mozgo_boy** — дата и время будут объявлены там же.\n\n"
        "**Один участник** может купить неограниченное количество попыток — чем больше билетов, тем выше шанс выиграть.\n\n"
        "💡 *Чем больше правильных ответов в квизе, тем больше бонусных билетов ты получаешь — и тем выше твой шанс на iPhone 17!*"
    )
    await message.answer(rules_text, parse_mode="Markdown", disable_web_page_preview=True)

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
