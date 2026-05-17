from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from config import OWNER_ID
from database.db_admin import get_total_users_count
from database.db import DB_PATH
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
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

@router.message(F.text == "👥 Пользователи (БД)")
async def admin_users(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    count = await get_total_users_count()
    await message.answer(f"📊 Всего пользователей в базе: <b>{count}</b>",
                         reply_markup=get_db_download_keyboard(),
                         parse_mode="HTML")

@router.callback_query(F.data == "download_db")
async def download_db(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    if os.path.exists(DB_PATH):
        await callback.message.answer_document(FSInputFile(DB_PATH), caption="📂 Актуальная база данных")
    else:
        await callback.answer("Файл базы данных не найден", show_alert=True)

    await callback.answer()

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("ℹ️ Здесь будет информация о победителе")

@router.message(F.text == "🔙 Назад в главное меню")
async def back_to_main(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("Переходим в главное меню...", reply_markup=await get_main_menu_keyboard(message.from_user.id))
