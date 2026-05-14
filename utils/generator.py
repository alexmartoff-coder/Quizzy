import random
import logging
from data.questions_pool import QUESTIONS_POOL

async def generate_questions(amount=10):
    # === FIXED: РАНДОМИЗАЦИЯ КВИЗА ===
    # Выбираем случайные вопросы из большого пула
    logging.info(f"Selecting {amount} random questions from the pool of {len(QUESTIONS_POOL)}")

    selected_questions = random.sample(QUESTIONS_POOL, min(amount, len(QUESTIONS_POOL)))

    final_questions = []
    prefix = ["A. ", "B. ", "C. ", "D. "]

    for q in selected_questions:
        # Создаем копию вопроса, чтобы не менять оригинал в пуле
        q_copy = q.copy()

        # Перемешиваем варианты ответов
        options = q_copy["options"].copy()
        correct_option = options[q_copy["correct_index"]]
        random.shuffle(options)

        # Обновляем правильный индекс после перемешивания
        q_copy["correct_index"] = options.index(correct_option)

        # Добавляем буквы A, B, C, D к вариантам
        formatted_options = []
        for i, opt in enumerate(options):
            formatted_options.append(f"{prefix[i]}{opt}")

        q_copy["options"] = formatted_options

        # Добавляем уникальный ID
        q_copy["id"] = random.randint(1000, 9999)

        final_questions.append(q_copy)

    return final_questions
