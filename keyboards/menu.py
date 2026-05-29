import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, has_user_used_free_attempt, get_paid_tickets_count
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import has_accepted_rules
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()
    paid_count = await get_paid_tickets_count()

    # Визуальный счетчик
    display_count = paid_count + INITIAL_FAKE_TICKETS
    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    progress_text = f"📊 До розыгрыша осталось: {display_count} из {TICKET_LIMIT} заявок\n{bar} {percent}%"

    if closed:
        progress_text = f"📢 Сбор заявок завершён!\nВсего заявок: {display_count}\n{bar} 100%"

    if not closed and rules_accepted:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    buttons.append([KeyboardButton(text="📜 Правила розыгрыша")])
    buttons.append([KeyboardButton(text="🎟️ Мои билеты")])
    buttons.append([KeyboardButton(text="🏆 Лидерборд")])
    buttons.append([KeyboardButton(text="❓ Поддержка")])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_participation_keyboard(show_free: bool):
    buttons = []
    if show_free:
        buttons.append([InlineKeyboardButton(text="🆓 Использовать бесплатную попытку", callback_data="use_free_attempt")])

    buttons.append([InlineKeyboardButton(text="💰 Поддержать (99 ₽)", callback_data="pay_99_rub")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
        [KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_db_download_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать базу данных (SQLITE)", callback_data="download_db")]
    ])

def get_start_quiz_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квиз", callback_data="start_quiz")]
    ])

def get_rules_agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я ознакомлен и согласен", callback_data="accept_rules")]
    ])
