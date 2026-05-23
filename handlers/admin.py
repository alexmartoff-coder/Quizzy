from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from config import OWNER_ID
from database.db_admin import get_all_users_data
from database.db import DB_PATH
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
from utils.google_sheets import export_to_google_sheets
import os

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("🛠 <b>Панель администратора</b>",
                         reply_markup=get_admin_keyboard(),
                         parse_mode="HTML")

@router.message(F.text == "📊 Экспорт в Google Sheets")
async def admin_export_google(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    status_msg = await message.answer("⏳ Подготовка данных и выгрузка в Google Sheets...")

    data = await get_all_users_data()
    url, error = await export_to_google_sheets(data)

    if error:
        await status_msg.edit_text(f"❌ Ошибка при экспорте:\n{error}")
    else:
        await status_msg.edit_text(f"✅ Данные успешно выгружены!\n\n🔗 <a href='{url}'>Открыть Google Таблицу</a>",
                                  parse_mode="HTML",
                                  disable_web_page_preview=False)

@router.message(F.text == "🏁 Управление Финалом")
async def admin_final_management(message: Message):
    if message.from_user.id != OWNER_ID: return
    from database.db_final import get_final_stats
    stats = await get_final_stats()
    text = (
        f"🏁 <b>Управление Финалом</b>\n\n"
        f"Всего финалистов (заявок): {stats['total_finalist_tickets']}\n"
        f"Зарегистрировалось: {stats['registered_tickets']} (юзеров: {stats['registered_users']})\n"
        f"Завершили прохождение: {stats['finished_tickets']}\n"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Рассчитать итоги", callback_data="admin_calc_final")],
        [InlineKeyboardButton(text="🚀 Тест: Запустить регистрацию (на 5 мин)", callback_data="admin_test_final_reg")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_calc_final")
async def admin_calc_final(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from database.db_winner import get_preliminary_winner, check_for_ties
    winner = await get_preliminary_winner()
    ties = await check_for_ties()

    if not winner:
        await callback.message.answer("Результатов финала пока нет.")
    elif ties:
        await callback.message.answer(f"⚠️ <b>Выявлено равенство результатов!</b>\nНужен мини-квиз для {len(ties)} заявок.", parse_mode="HTML")
    else:
        # Победитель определен
        from database.db import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
                u = await c.fetchone()
                name = u[0] if u[0] else u[1]

        text = (
            f"🏆 <b>Победитель определён!</b>\n\n"
            f"Участник: {name} (@{u[0]})\n"
            f"Заявка: №{winner[0]:05d}\n"
            f"Результат: {winner[2]}/8\n"
            f"Время: {winner[3]:.2f} сек."
        )
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_final_reg")
async def admin_test_final_reg(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    # Устанавливаем closed_at на "вчера 18:58", чтобы сейчас была регистрация (19:00 - 19:30)
    from datetime import datetime, timedelta
    fake_closed = datetime.now() - timedelta(days=1, minutes=2)
    import aiosqlite
    from database.db import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('closed_at', ?)", (fake_closed.isoformat(),))
        await db.commit()
    await callback.answer("Тестовый режим регистрации включен!", show_alert=True)

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("ℹ️ Здесь будет информация о победителе.\nДля полной выгрузки используйте кнопку выше.",
                         reply_markup=get_db_download_keyboard())

@router.callback_query(F.data == "download_db")
async def download_db(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    if os.path.exists(DB_PATH):
        await callback.message.answer_document(FSInputFile(DB_PATH), caption="📂 Актуальная база данных (SQLite)")
    else:
        await callback.answer("Файл базы данных не найден", show_alert=True)

    await callback.answer()

@router.message(F.text == "🔙 Назад в главное меню")
async def back_to_main(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    kb, progress = await get_main_menu_keyboard(message.from_user.id)
    await message.answer(f"{progress}\n\nПереходим в главное меню...", reply_markup=kb)
