import random
import logging
from data.questions_pool import QUESTIONS_POOL

async def generate_questions(amount=10):
    # Временно отключаем внешний API и используем локальный русский пул
    logging.info("Selecting questions from local Russian pool")
    return random.sample(QUESTIONS_POOL, amount)
