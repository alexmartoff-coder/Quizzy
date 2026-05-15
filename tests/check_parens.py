from data.questions_pool import QUESTIONS_POOL

for i, q in enumerate(QUESTIONS_POOL):
    correct_opt = q["options"][q["correct_index"]]
    if "(" in correct_opt or ")" in correct_opt:
        print(f"Question {i} correct option has parens: {correct_opt}")
    for opt in q["options"]:
        if "(" in opt or ")" in opt:
             print(f"Question {i} option has parens: {opt}")
