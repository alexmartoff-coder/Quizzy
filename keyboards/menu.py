from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, has_user_used_free_attempt, get_total_tickets_count, get_paid_tickets_count
from database.db_final import is_final_registration_open, has_user_registered_for_final, get_user_finalist_tickets, is_final_active
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import has_accepted_rules
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()
    paid_count = await get_paid_tickets_count()

    # Визуальный счетчик
    display_count = max(paid_count, INITIAL_FAKE_TICKETS)
    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    if not closed:
        progress_text = f"📊 До Финала осталось: {display_count} из {TICKET_LIMIT} заявок\n{bar} {percent}%"
    elif await is_final_active():
        from database.db_final import get_final_stats, get_final_times
        from datetime import datetime
        stats = await get_final_stats()
        times = await get_final_times()
        remaining = times["final_end"] - datetime.now()
        rem_str = str(remaining).split(".")[0]
        progress_text = (
            f"🏆 <b>ФИНАЛ В РАЗГАРЕ!</b>\n"
            f"Зарегистрировано заявок: {stats['registered_tickets']}\n"
            f"Завершено: {stats['finished_tickets']}\n"
            f"⏳ До окончания: {rem_str}"
        )

        if await is_final_registration_open():
            tickets = await get_user_finalist_tickets(user_id)
            if tickets and not await has_user_registered_for_final(user_id):
                buttons.append([KeyboardButton(text="🏆 Войти в Финал")])
    else:
        progress_text = "📢 Приём заявок завершён\n⏳ До Финала: 00:00:00"

    if not closed and rules_accepted:
        used_free = await has_user_used_free_attempt(user_id)
        if not used_free:
            buttons.append([KeyboardButton(text="🆓 Бесплатная заявка на участие")])

        buttons.append([KeyboardButton(text="💰 Поддержать (99 ₽)")])
        buttons.append([KeyboardButton(text="📊 Лидерборд")])
    elif not closed and not rules_accepted:
        # If rules not accepted, we don't show participation buttons
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
