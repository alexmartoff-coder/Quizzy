from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from database.db import add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure, get_paid_tickets_count, has_user_used_free_attempt, get_user_applications
from keyboards.menu import get_main_menu_keyboard
import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"{progress}\n\n"
        "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!\n\n"
        "Каждый участник получает 1 бесплатную заявку на участие.\n"
        "Вы также можете поддержать конкурс и получить дополнительную попытку (99 ₽).",
        reply_markup=kb
    )

@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Приложение к правилам для конкурса «iPhone 17 PRO 256 Гб»</b>\n\n"
        "Интеллектуальный конкурс «iPhone 17 PRO 256 Гб»\n"
        "<b>Тематика квиза:</b> компания Apple, её устройства, операционные системы, технологии, история.\n"
        "<b>Приз:</b> iPhone 17 PRO 256 Гб (один экземпляр).\n"
        "<b>Количество платных заявок для завершения Отборочного Этапа:</b> 3500. Бесплатные заявки не влияют на окончание приёма.\n"
        "<b>Старт Отборочного этапа:</b> 27 мая 2026 г. в 12:00 МСК.\n"
        "<b>Окончание Отборочного Этапа:</b> автоматически при достижении 3500 платных заявок.\n"
        "<b>Финал:</b> следующий календарный день после завершения Отборочного этапа в 19:00 по московскому времени.\n\n"
        "Все остальные условия — в соответствии с Основными правилами интеллектуальных конкурсов, размещённых по ссылке:\n"
        "https://cbda.ru/rules/base\n\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100. (самозанятый)."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    # Получаем заявки с информацией о типе (платная/бесплатная)
    from database.db import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number, status, score, type FROM tickets WHERE user_id = ? ORDER BY created_at", (message.from_user.id,)) as cursor:
            apps = await cursor.fetchall()

    if not apps:
        await message.answer("У тебя пока нет заявок. Используй бесплатную попытку в меню!")
    else:
        text = "<b>Твои заявки:</b>\n\n"
        for t_num, status, score, t_type in apps:
            type_tag = " (Платная)" if t_type == "paid" else ""
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            elif status == "finalist":
                status_text = "— прошла в Финал!"
                score_text = f"\nРезультат: {score}/10"
            else:
                status_text = "— Не прошла в финал"
                score_text = f"\nРезультат: {score}/10"

            text += f"🎫 №{t_num:05d}{type_tag} {status_text}{score_text}\n\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📊 Лидерборд")
@router.message(F.text == "📊 Лидерборд финалистов")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд финалистов пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству финалистских заявок:</b>\n\n"
    for i, (username, full_name, finalist_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{finalist_count}</b> фин. заявок\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")
