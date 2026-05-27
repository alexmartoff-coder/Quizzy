import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, has_user_used_free_attempt, get_total_tickets_count, get_paid_tickets_count
from database.db_final import is_final_registration_open, has_user_registered_for_final, get_user_finalist_tickets, is_final_active
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS
from utils.time_utils import get_moscow_now

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import has_accepted_rules, get_total_tickets_count
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()
    total_count = await get_total_tickets_count()

    display_count = total_count
    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    if not closed:
        progress_text = f"📊 Собрано билетов: {display_count} из {TICKET_LIMIT}\n{bar} {percent}%"
    else:
        progress_text = f"🎉 Сбор билетов завершён досрочно!\n\nМы набрали {display_count}+ билетов. Спасибо всем участникам!"

    if not closed and rules_accepted:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    buttons.append([KeyboardButton(text="📊 Лидерборд")])

    buttons.extend([
        [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="📜 Правила розыгрыша")],
        [KeyboardButton(text="📞 Поддержка")]
    ])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
        [KeyboardButton(text="🏁 Управление Финалом")],
        [KeyboardButton(text="🏆 Победитель")],
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
