from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
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
        [InlineKeyboardButton(text="🚀 Тест: Регистрация СЕЙЧАС", callback_data="admin_test_reg_now")],
        [InlineKeyboardButton(text="🏁 Тест: Финал СЕЙЧАС", callback_data="admin_test_final_now")],
        [InlineKeyboardButton(text="⏰ Тест: Завершить Финал", callback_data="admin_test_finish_now")],
        [InlineKeyboardButton(text="❌ Сброс тестов", callback_data="admin_test_reset")],
        [InlineKeyboardButton(text="🛠 Сид тестовых данных (3495)", callback_data="admin_seed_data")]
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

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Опубликовать итоги в канал", callback_data="admin_publish_results")]
        ])
        await callback.message.answer("Опубликовать результаты?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_seed_data")
async def admin_seed_data_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from tests.seed_test_data import seed_data
    await seed_data()
    await callback.message.answer("✅ База данных засеяна (3495 заявок)!")
    await callback.answer()

@router.callback_query(F.data == "admin_test_reg_now")
async def admin_test_reg_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(minutes=1) # Уже идет 1 минуту
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()
    await callback.message.answer("🚀 <b>Тест: Регистрация запущена!</b>\nПроверьте главное меню.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_final_now")
async def admin_test_final_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(minutes=31) # Регистрация закончилась 1 мин назад
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()
    await callback.message.answer("🏁 <b>Тест: Финал запущен!</b>\nПроверьте главное меню.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_finish_now")
async def admin_test_finish_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(hours=2, minutes=1) # Финал закончился 1 мин назад
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()
    await callback.message.answer("⏰ <b>Тест: Финал завершен!</b>\nТеперь можно рассчитать итоги.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_reset")
async def admin_test_reset(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM settings WHERE key = 'test_reg_start'")
        await db.commit()
    await callback.message.answer("❌ Тестовые настройки сброшены.")
    await callback.answer()

@router.callback_query(F.data == "admin_publish_results")
async def admin_publish_results(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return

    from database.db_winner import get_preliminary_winner
    winner = await get_preliminary_winner()
    if not winner: return

    from database.db_final import get_final_stats
    stats = await get_final_stats()

    from database.db import DB_PATH, CHANNEL_ID
    import aiosqlite
    import random

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
            u = await c.fetchone()
            username = u[0] if u[0] else u[1]

        # Генерация 6-значного кода
        win_code = "".join([str(random.randint(0,9)) for _ in range(6)])
        await db.execute("INSERT OR REPLACE INTO winners (user_id, ticket_number, code) VALUES (?, ?, ?)",
                         (winner[1], winner[0], win_code))
        await db.commit()

    text = (
        f"🎉 <b>ФИНАЛ ЗАВЕРШЁН!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"Всего финалистских заявок: {stats['total_finalist_tickets']}\n"
        f"Зарегистрировалось (нажали кнопку): {stats['registered_tickets']}\n"
        f"Не зарегистрировалось: {stats['total_finalist_tickets'] - stats['registered_tickets']}\n"
        f"Успешно прошли финал: {stats['finished_tickets']}\n"
        f"Не завершили прохождение: {stats['registered_tickets'] - stats['finished_tickets']}\n\n"
        f"🏆 <b>ПОБЕДИТЕЛЬ:</b> @{u[0]} (заявка №{winner[0]:05d})\n"
        f"Результат: {winner[2]}/8, время {winner[3]:.2f} сек.\n"
        f"Приз: iPhone 17 PRO 256 Гб"
    )

    # В канал
    try: await callback.bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    except: pass

    # Победителю
    win_msg = (
        f"🎊 <b>ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ В КОНКУРСЕ!</b>\n\n"
        f"Ваш приз: <b>iPhone 17 PRO 256 Гб</b>\n"
        f"Ваш секретный код: <code>{win_code}</code>\n\n"
        f"<b>Инструкция:</b>\n"
        f"1. Свяжитесь с организатором alexandr@cbda.ru или напишите в поддержку.\n"
        f"2. Сообщите ваш секретный код.\n"
        f"3. Подготовьте данные для акта приёма-передачи."
    )
    try: await callback.bot.send_message(winner[1], win_msg, parse_mode="HTML")
    except: pass

    # Админу
    await callback.message.answer(f"✅ Результаты опубликованы!\nКод победителя: {win_code}")
    await callback.answer()

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
