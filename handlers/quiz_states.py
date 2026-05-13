from aiogram.fsm.state import State, StatesGroup
import os
import random

class QuizStates(StatesGroup):
    answering = State()

# === БОЛЬШОЙ ПУЛ ВОПРОСОВ ===
# Заменяем загрузку из JSON на импорт из пула
try:
    from data.questions_pool import QUESTIONS_POOL
    QUESTIONS = QUESTIONS_POOL
except ImportError:
    # Fallback if pool file is missing
    QUESTIONS = []
