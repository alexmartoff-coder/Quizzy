from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.quiz_states import QuizStates
from database.db import get_quiz_session, update_quiz_score, update_quiz_question, finish_quiz_session, increment_ticket_id, add_ticket, get_total_tickets_count, close_collection, is_collection_closed
from keyboards.menu import get_main_menu_keyboard
from utils.generator import generate_questions
import asyncio
import time
import logging
from config import TICKET_LIMIT, CHANNEL_ID

router = Router()

# Глобальный реестр таймеров для предотвращения утечек и зависаний
# Ключ: user_id, Значение: asyncio.Task
active_quiz_timers = {}

def build_keyboard(question, q_idx):
    """Создает клавиатуру с вариантами ответов и индексом вопроса для валидации."""
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            text=option,
            callback_data=f"qans_{question['id']}_{i}_{q_idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def safe_send_question(bot: Bot, state: FSMContext, user_id: int, q_idx: int):
    """
    Безопасная отправка вопроса.
    Управляет состоянием и жизненным циклом таймера.
    """
    logging.info(f"SAFE_SEND: User {user_id}, Q_idx {q_idx}")

    # 1. Очистка старого таймера (важно: не отменяем текущую задачу, если мы в ней)
    current_task = asyncio.current_task()
    if user_id in active_quiz_timers:
        old_task = active_quiz_timers[user_id]
        if old_task != current_task:
            old_task.cancel()
            logging.debug(f"Cancelled previous timer for user {user_id}")
        active_quiz_timers.pop(user_id, None)

    # 2. Получение данных квиза
    data = await state.get_data()
    questions = data.get("current_questions")

    if not questions or q_idx >= len(questions):
        logging.info(f"Quiz end for {user_id}. Finalizing...")
        await finish_quiz_logic(bot, state, user_id)
        return

    # 3. УСТАНОВКА СОСТОЯНИЯ ПЕРЕД ОТПРАВКОЙ
    # Это критически важно для предотвращения игнорирования быстрых ответов
    await state.set_state(QuizStates.answering)
    await state.update_data(current_question_index=q_idx)

    question = questions[q_idx]
    text = f"❓ **Вопрос {q_idx + 1}/10**\n\n{question['question']}\n\n⏱ У тебя 30 секунд!"

    try:
        # 4. Отправка сообщения пользователю
        msg = await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=build_keyboard(question, q_idx),
            parse_mode="Markdown"
        )

        # 5. Сохранение ID сообщения и времени старта
        await state.update_data(
            question_msg_id=msg.message_id,
            start_time=time.time()
        )

        # 6. Запуск нового фонового таймера
        timer_task = asyncio.create_task(quiz_timer_logic(bot, state, user_id, q_idx, msg.message_id))
        active_quiz_timers[user_id] = timer_task

    except Exception as e:
        logging.error(f"Error sending question to {user_id}: {e}")
        await bot.send_message(user_id, "⚠️ Ошибка связи. Попробуйте нажать 'Мои билеты' -> 'Играть', чтобы продолжить.")

async def quiz_timer_logic(bot: Bot, state: FSMContext, user_id: int, q_idx: int, msg_id: int):
    """Фоновая задача, ожидающая 30 секунд."""
    try:
        await asyncio.sleep(30)

        # Проверяем: актуально ли еще это ожидание?
        current_state = await state.get_state()
        data = await state.get_data()

        if current_state == QuizStates.answering and data.get("current_question_index") == q_idx:
            logging.info(f"TIMEOUT: User {user_id} on Q {q_idx}")

            # Блокируем ввод СРАЗУ
            await state.set_state(None)

            # Очистка кнопок у старого вопроса
            try:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
            except Exception: pass

            questions = data.get("current_questions")
            question = questions[q_idx]

            # Уведомление о таймауте
            await bot.send_message(
                chat_id=user_id,
                text=f"⏰ **Время вышло!**\n\n❌ Правильный ответ: {question['options'][question['correct_index']]}\n\n{question['explanation']}",
                parse_mode="Markdown"
            )

            # Переход к следующему вопросу
            next_idx = q_idx + 1
            await update_quiz_question(user_id, next_idx)

            # Важно: вызываем через безопасную функцию
            await safe_send_question(bot, state, user_id, next_idx)

    except asyncio.CancelledError:
        logging.debug(f"Timer for user {user_id} was cancelled correctly.")
    except Exception as e:
        logging.error(f"Error in timer logic for {user_id}: {e}")
    finally:
        # Удаляем задачу из реестра, если она текущая
        if active_quiz_timers.get(user_id) == asyncio.current_task():
            active_quiz_timers.pop(user_id, None)

@router.callback_query(F.data == "start_quiz")
async def start_quiz_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = await get_quiz_session(user_id)

    if not session or not session[2]: # session[2] is is_active
        await callback.answer("Сначала оплатите участие!", show_alert=True)
        return

    await callback.answer()
    loading = await callback.message.answer("🔄 Подбираем вопросы специально для тебя...")

    try:
        # Генерация 10 случайных вопросов из пула
        questions = await generate_questions(10)
        await state.update_data(current_questions=questions)

        try: await loading.delete()
        except Exception: pass

        # Запуск первого вопроса
        await safe_send_question(callback.bot, state, user_id, 0)
    except Exception as e:
        logging.error(f"Start quiz failed for {user_id}: {e}")
        await callback.message.answer("⚠️ Ошибка при запуске. Попробуйте еще раз.")

@router.callback_query(QuizStates.answering, F.data.startswith("qans_"))
async def process_quiz_answer(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора ответа пользователем."""
    # 1. Убираем спиннер с кнопки
    await callback.answer()

    user_id = callback.from_user.id
    data = await state.get_data()

    # 2. Проверка соответствия индекса вопроса (защита от кликов по старым сообщениям)
    try:
        parts = callback.data.split("_")
        ans_idx = int(parts[2])
        q_idx_in_cb = int(parts[3])
    except (IndexError, ValueError):
        return

    current_q_idx = data.get("current_question_index")
    if q_idx_in_cb != current_q_idx:
        logging.warning(f"IGNORE: User {user_id} clicked old button Q{q_idx_in_cb}")
        return

    # 3. ОСТАНОВКА ТАЙМЕРА (пользователь успел ответить)
    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done():
            task.cancel()

    # 4. БЛОКИРОВКА СОСТОЯНИЯ (защита от двойного клика)
    await state.set_state(None)

    # 5. Очистка кнопок
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception: pass

    # 6. Проверка правильности
    questions = data.get("current_questions")
    if not questions: return
    question = questions[current_q_idx]

    is_correct = ans_idx == question['correct_index']
    if is_correct:
        session = await get_quiz_session(user_id)
        new_score = (session[0] if session else 0) + 1
        await update_quiz_score(user_id, new_score)
        res_text = f"✅ **Верно!**\n\n{question['explanation']}"
    else:
        res_text = f"❌ **Неверно.** Правильный ответ: {question['options'][question['correct_index']]}\n\n{question['explanation']}"

    await callback.message.answer(res_text, parse_mode="Markdown")

    # 7. Переход к следующему
    next_idx = current_q_idx + 1
    await update_quiz_question(user_id, next_idx)

    # Короткая пауза для комфортного чтения объяснения
    await asyncio.sleep(1.5)
    await safe_send_question(callback.bot, state, user_id, next_idx)

@router.callback_query(F.data.startswith("qans_"))
async def catch_expired_clicks(callback: CallbackQuery):
    """Обработчик нажатий, если состояние не активно (старые вопросы)."""
    await callback.answer("Этот вопрос уже не активен.", show_alert=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception: pass

async def finish_quiz_logic(bot: Bot, state: FSMContext, user_id: int):
    """Завершение квиза и начисление билетов."""
    logging.info(f"FINISH: User {user_id}")

    # Финальная очистка таймеров
    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done():
            task.cancel()

    session = await get_quiz_session(user_id)
    score = session[0] if session else 0

    # Расчет бонусов
    bonus = 0
    if score == 10: bonus = 3
    elif score == 9: bonus = 2
    elif score == 8: bonus = 1

    msg_parts = [f"🏁 **Квиз завершён!**\n\nТвой результат: **{score}/10**"]

    if bonus > 0:
        start_id = await increment_ticket_id(bonus)
        for i in range(bonus):
            await add_ticket(user_id, start_id + i, "bonus")
        msg_parts.append(f"🎉 Ты получаешь **{bonus} бонусных билетов** (№{start_id} - №{start_id + bonus - 1})!")
    else:
        msg_parts.append("Бонусных билетов в этот раз нет. Попробуй еще раз!")

    # Сброс сессии
    await finish_quiz_session(user_id)
    await state.clear()

    try:
        await bot.send_message(
            chat_id=user_id,
            text="\n\n".join(msg_parts),
            reply_markup=await get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception: pass

    # Проверка лимита 2500
    total = await get_total_tickets_count()
    if total >= TICKET_LIMIT:
        if not await is_collection_closed():
            await close_collection()
            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text="🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\nЛимит в 2500 билетов достигнут. Всем спасибо!"
                )
            except Exception: pass
