from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from handlers.quiz_states import QuizStates, QUESTIONS
from database.db import get_quiz_session, update_quiz_score, update_quiz_question, finish_quiz_session, increment_ticket_id, add_ticket, get_total_tickets_count, close_collection, is_collection_closed
from keyboards.menu import get_main_menu_keyboard
from utils.generator import generate_questions
import asyncio
import time
import random
from config import TICKET_LIMIT, BOT_TOKEN, CHANNEL_ID
from aiogram import Bot
import logging

router = Router()

def get_question_keyboard(question_id, options, question_index):
    keyboard = []
    for i, option in enumerate(options):
        # Добавляем question_index в callback_data для верификации
        keyboard.append([InlineKeyboardButton(text=option, callback_data=f"answer_{question_id}_{i}_{question_index}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_question(message: Message, state: FSMContext, question_index: int, user_id: int):
    data = await state.get_data()
    # === FIXED: РАНДОМИЗАЦИЯ КВИЗА ===
    current_questions = data.get("current_questions")

    if not current_questions or question_index >= len(current_questions):
        await finish_quiz(message, state, user_id)
        return

    # Cancel previous timeout if exists
    # === FIXED: ТАЙМАУТ ===
    prev_task = data.get("timeout_task")
    if prev_task and not prev_task.done():
        prev_task.cancel()

    question = current_questions[question_index]
    text = f"❓ **Вопрос {question_index + 1}/10**\n\n{question['question']}\n\n⏱ У тебя 30 секунд!"

    msg = await message.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=get_question_keyboard(question['id'], question['options'], question_index),
        parse_mode="Markdown"
    )

    # Start timeout task
    # === FIXED: ТАЙМАУТ ===
    timeout_task = asyncio.create_task(handle_timeout(message, state, question_index, msg.message_id, user_id))

    # Store start time, message id and task to handle timeout/cleanup
    await state.update_data(
        current_question_index=question_index,
        question_msg_id=msg.message_id,
        start_time=time.time(),
        timeout_task=timeout_task
    )
    await state.set_state(QuizStates.answering)

async def handle_timeout(message: Message, state: FSMContext, question_index: int, msg_id: int, user_id: int):
    # === FIXED: ТАЙМАУТ ===
    try:
        await asyncio.sleep(30)
        data = await state.get_data()

        # Check if we are still on the same question and haven't answered
        if (await state.get_state() == QuizStates.answering and
            data.get("current_question_index") == question_index and
            data.get("question_msg_id") == msg_id):

            # Timeout occurred
            current_questions = data.get("current_questions")
            question = current_questions[question_index]
            await message.bot.send_message(
                chat_id=user_id,
                text=f"⏰ Время вышло!\n\n❌ Правильный ответ: {question['options'][question['correct_index']]}\n\n{question['explanation']}"
            )

            # Move to next question
            await update_quiz_question(user_id, question_index + 1)
            await send_question(message, state, question_index + 1, user_id)
    except asyncio.CancelledError:
        pass # Task cancelled because user answered

@router.callback_query(F.data == "start_quiz")
async def start_quiz_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = await get_quiz_session(user_id)
    if not session or not session[2]: # session[2] is is_active
        await callback.answer("У тебя нет активной сессии квиза. Оплати участие!", show_alert=True)
        return

    await callback.answer()

    # === FIXED: РАНДОМИЗАЦИЯ КВИЗА ===
    await callback.message.answer("🔄 Подбираем вопросы специально для тебя...")
    current_questions = await generate_questions(10)
    await state.update_data(current_questions=current_questions)

    await send_question(callback.message, state, 0, user_id)

@router.callback_query(QuizStates.answering, F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    # ВСЕГДА отвечаем на callback, чтобы убрать "загрузку"
    await callback.answer()

    user_id = callback.from_user.id
    data = await state.get_data()

    parts = callback.data.split("_")
    # answer_{id}_{index}_{question_index}
    question_id = int(parts[1])
    answer_index = int(parts[2])
    cb_question_index = int(parts[3])

    current_question_index = data.get("current_question_index")

    # Игнорируем ответы на старые вопросы
    if cb_question_index != current_question_index:
        return

    # Cancel timeout task as soon as valid answer is received
    # === FIXED: ТАЙМАУТ ===
    timeout_task = data.get("timeout_task")
    if timeout_task and not timeout_task.done():
        timeout_task.cancel()

    current_questions = data.get("current_questions")
    question = current_questions[current_question_index]

    if question['id'] != question_id:
        return

    # Check time (with small grace period)
    if time.time() - data.get("start_time", 0) > 31:
        # Хотя handle_timeout должен был сработать, на всякий случай
        return

    await state.set_state(None) # Stop answering

    is_correct = answer_index == question['correct_index']
    if is_correct:
        session = await get_quiz_session(user_id)
        new_score = session[0] + 1
        await update_quiz_score(user_id, new_score)
        response = f"✅ Верно!\n\n{question['explanation']}"
    else:
        response = f"❌ Неверно. Правильный ответ: {question['options'][question['correct_index']]}\n\n{question['explanation']}"

    await callback.message.answer(response)

    # Move to next question
    next_index = current_question_index + 1
    await update_quiz_question(user_id, next_index)
    await send_question(callback.message, state, next_index, user_id)

async def finish_quiz(message: Message, state: FSMContext, user_id: int):
    session = await get_quiz_session(user_id)
    score = session[0]

    bonus_tickets = 0
    if score == 10:
        bonus_tickets = 3
    elif score == 9:
        bonus_tickets = 2
    elif score == 8:
        bonus_tickets = 1

    total_new_tickets = bonus_tickets
    start_ticket_id = 0
    if total_new_tickets > 0:
        start_ticket_id = await increment_ticket_id(total_new_tickets)
        for i in range(total_new_tickets):
            await add_ticket(user_id, start_ticket_id + i, "bonus")

    await finish_quiz_session(user_id)
    await state.clear()

    result_text = f"🏁 Квиз завершён!\n\nТвой результат: {score}/10\n"
    if bonus_tickets > 0:
        result_text += f"🎉 Ты получаешь {bonus_tickets} бонусных билетов (№{start_ticket_id} - №{start_ticket_id + bonus_tickets - 1})!"
    else:
        result_text += "К сожалению, в этот раз без бонусов. Попробуй еще раз!"

    await message.bot.send_message(chat_id=user_id, text=result_text, reply_markup=await get_main_menu_keyboard())

    # Check limit and announce
    total_tickets = await get_total_tickets_count()
    if total_tickets >= TICKET_LIMIT:
        if not await is_collection_closed():
            await close_collection()
            # Send to channel using the bot instance from the message
            try:
                await message.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                         "Мы достигли лимита в 2500 билетов раньше срока.\n"
                         "Спасибо всем, кто принял участие!\n\n"
                         "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
                )
            except Exception as e:
                logging.error(f"Failed to send to channel: {e}")
