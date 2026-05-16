from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, get_user_tickets, get_leaderboard, is_collection_closed, check_and_trigger_closure
from keyboards.menu import get_main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    # Проактивная проверка закрытия (например, по дате) при старте
    await check_and_trigger_closure(message.bot)
    await message.answer(
        "Добро пожаловать в квиз @googlestop_bot!\n\n"
        "Участвуй в розыгрыше iPhone 17. Один билет стоит 99 ₽. "
        "За хороший результат в квизе можно получить до +3 бонусных билетов!",
        reply_markup=await get_main_menu_keyboard()
    )

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    # Используем HTML для надежности отображения
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "Участие — платное. Стоимость одной попытки — <b>99 ₽</b>.\n\n"
        "За каждую оплату вы получаете:\n\n"
        "✅ 1 гарантированный билет\n\n"
        "🎁 до +3 бонусных билетов в зависимости от результата квиза:\n\n"
        "10/10 правильных → +3 билета\n"
        "9/10 → +2 билета\n"
        "8/10 → +1 билет\n"
        "менее 8 → бонусов нет\n\n"
        "<b>Все билеты</b> (базовые + бонусные) участвуют в розыгрыше.\n\n"
        "<b>Сбор билетов</b> автоматически прекращается, как только набрано <b>2500 билетов</b>.\n\n"
        "После остановки сбора:\n"
        "❌ играть и оплачивать нельзя\n"
        "✅ можно посмотреть свои билеты, лидерборд и правила\n\n"
        "Лидерборд отображает 20 лучших участников.\n\n"
        "Розыгрыш проводится честно через генератор случайных чисел random.org.\n\n"
        "Номер билета присваивается рондомно.\n\n"
        "Прямой эфир с определением победителя состоится в канале @mozgo_boy — дата и время будут объявлены там же.\n\n"
        "Один участник может купить неограниченное количество попыток — чем больше билетов, тем выше шанс выиграть.\n\n"
        "💡 <i>Чем больше правильных ответов в квизе, тем больше бонусных билетов ты получаешь — и тем выше твой шанс на iPhone 17!</i>"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    tickets = await get_user_tickets(message.from_user.id)
    if not tickets:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы участвовать!")
    else:
        # Форматируем номера билетов как 4 цифры (0001, 0002 и т.д.)
        tickets_str = ", ".join([f"№{t:04d}" for t in tickets])
        await message.answer(f"Твои билеты ({len(tickets)} шт.):\n{tickets_str}")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    # Отображаем топ-20 лидеров
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, total, base, bonus) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{total}</b> бил. ({base} купл. + {bonus} бонус.)\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь к @mozgo_boy_admin")
