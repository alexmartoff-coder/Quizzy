from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, get_paid_tickets_count, has_user_used_free_attempt
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    closed = await is_collection_closed()
    paid_count = await get_paid_tickets_count()

    # Визуальный счетчик с фейковым стартом (0741)
    if paid_count < INITIAL_FAKE_TICKETS:
        display_count = INITIAL_FAKE_TICKETS
    else:
        display_count = paid_count

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    if not closed:
        progress_text = f"📊 До Финала осталось: {display_count} из {TICKET_LIMIT} заявок\n{bar} {percent}%"
    else:
        progress_text = "📢 Приём заявок завершён\n⏳ До Финала: 00:29:59"

    buttons = []

    if not closed:
        used_free = await has_user_used_free_attempt(user_id)
        if not used_free:
            buttons.append([KeyboardButton(text="🆓 Бесплатная заявка на участие")])

        buttons.append([KeyboardButton(text="💰 Поддержать (99 ₽)")])
        buttons.append([KeyboardButton(text="📊 Лидерборд")])
    else:
        buttons.append([KeyboardButton(text="📊 Лидерборд финалистов")])

    buttons.extend([
        [KeyboardButton(text="👤 Мои заявки"), KeyboardButton(text="❓ Правила конкурса")],
        [KeyboardButton(text="📞 Поддержка")]
    ])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_start_quiz_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квиз", callback_data="start_quiz")]
    ])

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
        [KeyboardButton(text="🏆 Победитель")],
        [KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_db_download_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать базу данных (SQLITE)", callback_data="download_db")]
    ])
