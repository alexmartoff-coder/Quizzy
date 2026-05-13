from aiogram.fsm.state import State, StatesGroup
import json
import os

class QuizStates(StatesGroup):
    answering = State()

def load_questions():
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "questions.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = load_questions()
