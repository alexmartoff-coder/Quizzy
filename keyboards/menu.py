from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed

async def get_main_menu_keyboard():
    closed = await is_collection_closed()

    buttons = []
    if not closed:
        buttons.append([KeyboardButton(text="🎁 Участвовать в розыгрыше iPhone 17 PRO 256 Гб.")])

    buttons.extend([
        [KeyboardButton(text="📜 Правила розыгрыша"), KeyboardButton(text="🎟️ Мои билеты")],
        [KeyboardButton(text="🏆 Лидерборд"), KeyboardButton(text="❓ Поддержка")]
    ])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_start_quiz_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квиз", callback_data="start_quiz")]
    ])
