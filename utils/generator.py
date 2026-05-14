import aiohttp
import random
import html
import logging
from data.questions_pool import QUESTIONS_POOL

async def generate_questions(amount=10):
    url = f"https://opentdb.com/api.php?amount={amount}&type=multiple"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("response_code") == 0:
                        results = data.get("results")
                        generated_questions = []
                        for i, res in enumerate(results):
                            question_text = html.unescape(res["question"])
                            correct_answer = html.unescape(res["correct_answer"])
                            incorrect_answers = [html.unescape(ans) for ans in res["incorrect_answers"]]

                            options = incorrect_answers + [correct_answer]
                            random.shuffle(options)

                            correct_index = options.index(correct_answer)

                            generated_questions.append({
                                "id": 1000 + i, # Dummy ID for generated questions
                                "question": question_text,
                                "options": options,
                                "correct_index": correct_index,
                                "explanation": f"Правильный ответ: {correct_answer}. (Источник: Open Trivia DB)"
                            })
                        return generated_questions
                    else:
                        logging.warning(f"OpenTDB returned response code {data.get('response_code')}")
                else:
                    logging.warning(f"OpenTDB returned status {response.status}")
    except Exception as e:
        logging.error(f"Error generating questions: {e}")

    # Fallback to local pool if API fails or returns no results
    logging.info("Falling back to local question pool")
    return random.sample(QUESTIONS_POOL, amount)
