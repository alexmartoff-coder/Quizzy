from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed
from datetime import datetime
from config import DEADLINE_DATE

async def get_main_menu_keyboard():
    # ПРАВИЛА: Учитываем дату дедлайна в меню
    closed = await is_collection_closed() or datetime.now() > DEADLINE_DATE

    buttons = []
    if not closed:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    buttons.extend([
        [KeyboardButton(text="📜 Правила розыгрыша"), KeyboardButton(text="🎟️ Мои билеты")],
        [KeyboardButton(text="🏆 Лидерборд"), KeyboardButton(text="❓ Поддержка")]
    ])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

def get_start_quiz_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квиз", callback_data="start_quiz")]
    ])
