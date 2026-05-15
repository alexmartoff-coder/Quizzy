from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.quiz_states import QuizStates
from database.db import get_quiz_session, update_quiz_score, update_quiz_question, finish_quiz_session, issue_random_tickets, get_total_tickets_count, close_collection, is_collection_closed, check_and_trigger_closure
from keyboards.menu import get_main_menu_keyboard
from utils.generator import generate_questions
import asyncio
import time
import logging
from config import TICKET_LIMIT, CHANNEL_ID
import html

router = Router()

# Глобальный реестр таймеров
active_quiz_timers = {}

def build_keyboard(question, q_idx):
    keyboard = []
    for i, option in enumerate(question['options']):
        # Экранируем текст на всякий случай, хотя в кнопках это не нужно для HTML parse_mode сообщения
        keyboard.append([InlineKeyboardButton(
            text=option,
            callback_data=f"qans_{question['id']}_{i}_{q_idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def safe_send_question(bot: Bot, state: FSMContext, user_id: int, q_idx: int):
    logging.info(f"SAFE_SEND: User {user_id}, Q_idx {q_idx}")

    # 1. Очистка старого таймера
    current_task = asyncio.current_task()
    if user_id in active_quiz_timers:
        old_task = active_quiz_timers[user_id]
        if old_task != current_task:
            old_task.cancel()
        active_quiz_timers.pop(user_id, None)

    data = await state.get_data()
    questions = data.get("current_questions")

    if not questions or q_idx >= len(questions):
        await finish_quiz_logic(bot, state, user_id)
        return

    # 2. Установка состояния ПЕРЕД отправкой
    await state.set_state(QuizStates.answering)
    await state.update_data(current_question_index=q_idx)

    question = questions[q_idx]
    # Используем HTML для надежности
    q_text = html.escape(question['question'])
    text = f"❓ <b>Вопрос {q_idx + 1}/10</b>\n\n{q_text}\n\n⏱ У тебя 30 секунд!"

    try:
        msg = await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=build_keyboard(question, q_idx),
            parse_mode="HTML"
        )

        await state.update_data(
            question_msg_id=msg.message_id,
            start_time=time.time()
        )

        # 3. Запуск таймера
        timer_task = asyncio.create_task(quiz_timer_logic(bot, state, user_id, q_idx, msg.message_id))
        active_quiz_timers[user_id] = timer_task

    except Exception as e:
        logging.error(f"Error sending question to {user_id}: {e}")
        await bot.send_message(user_id, "⚠️ Произошла ошибка при отображении вопроса. Попробуйте продолжить через меню.")

async def quiz_timer_logic(bot: Bot, state: FSMContext, user_id: int, q_idx: int, msg_id: int):
    try:
        await asyncio.sleep(30)

        data = await state.get_data()
        current_state = await state.get_state()

        if current_state == QuizStates.answering and data.get("current_question_index") == q_idx:
            # Снимаем состояние, чтобы не было гонки
            await state.set_state(None)

            try:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
            except Exception: pass

            questions = data.get("current_questions")
            question = questions[q_idx]

            correct_text = html.escape(question['options'][question['correct_index']])
            expl_text = html.escape(question['explanation'])

            await bot.send_message(
                chat_id=user_id,
                text=f"⏰ <b>Время вышло!</b>\n\n❌ Правильный ответ: <b>{correct_text}</b>\n\n{expl_text}",
                parse_mode="HTML"
            )

            next_idx = q_idx + 1
            await update_quiz_question(user_id, next_idx)
            await safe_send_question(bot, state, user_id, next_idx)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Error in timer logic for {user_id}: {e}")
    finally:
        if active_quiz_timers.get(user_id) == asyncio.current_task():
            active_quiz_timers.pop(user_id, None)

@router.callback_query(F.data == "start_quiz")
async def start_quiz_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    session = await get_quiz_session(user_id)

    if not session or not session[2]:
        await callback.message.answer("Сначала оплатите участие!")
        return

    loading = await callback.message.answer("🔄 Подбираем вопросы...")

    try:
        questions = await generate_questions(10)
        await state.update_data(current_questions=questions)
        try: await loading.delete()
        except Exception: pass
        await safe_send_question(callback.bot, state, user_id, 0)
    except Exception as e:
        logging.error(f"Start quiz failed: {e}")
        await callback.message.answer("⚠️ Ошибка запуска.")

@router.callback_query(QuizStates.answering, F.data.startswith("qans_"))
async def process_quiz_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    data = await state.get_data()

    try:
        parts = callback.data.split("_")
        ans_idx = int(parts[2])
        q_idx_in_cb = int(parts[3])
    except: return

    if q_idx_in_cb != data.get("current_question_index"):
        return

    # Отмена таймера
    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done(): task.cancel()

    await state.set_state(None)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception: pass

    questions = data.get("current_questions")
    if not questions: return
    question = questions[q_idx_in_cb]

    is_correct = ans_idx == question['correct_index']
    correct_text = html.escape(question['options'][question['correct_index']])
    expl_text = html.escape(question['explanation'])

    if is_correct:
        session = await get_quiz_session(user_id)
        new_score = (session[0] if session else 0) + 1
        await update_quiz_score(user_id, new_score)
        res_text = f"✅ <b>Верно!</b>\n\n{expl_text}"
    else:
        res_text = f"❌ <b>Неверно.</b> Правильный ответ: <b>{correct_text}</b>\n\n{expl_text}"

    await callback.message.answer(res_text, parse_mode="HTML")

    next_idx = q_idx_in_cb + 1
    await update_quiz_question(user_id, next_idx)
    await asyncio.sleep(1.5)
    await safe_send_question(callback.bot, state, user_id, next_idx)

@router.callback_query(F.data.startswith("qans_"))
async def catch_expired_clicks(callback: CallbackQuery):
    await callback.answer("Этот вопрос уже не активен.", show_alert=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception: pass

async def finish_quiz_logic(bot: Bot, state: FSMContext, user_id: int):
    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done(): task.cancel()

    session = await get_quiz_session(user_id)
    score = session[0] if session else 0

    bonus = 0
    if score == 10: bonus = 3
    elif score == 9: bonus = 2
    elif score == 8: bonus = 1

    msg = f"🏁 <b>Квиз завершён!</b>\n\nТвой результат: <b>{score}/10</b>\n\n"

    if bonus > 0:
        issued = await issue_random_tickets(user_id, bonus, "bonus")
        if issued:
            if len(issued) == 1:
                msg += f"🎉 Ты получаешь <b>{len(issued)} бонусный билет</b> (№{issued[0]:04d})!"
            else:
                tickets_str = ", ".join([f"№{t:04d}" for t in issued])
                msg += f"🎉 Ты получаешь <b>{len(issued)} бонусных билета</b> ({tickets_str})!"
        else:
            msg += "Бонусные билеты закончились!"
    else:
        msg += "Бонусных билетов в этот раз нет. Попробуй еще раз!"

    await finish_quiz_session(user_id)
    await state.clear()

    await bot.send_message(
        chat_id=user_id,
        text=msg,
        reply_markup=await get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    await check_and_trigger_closure(bot)
