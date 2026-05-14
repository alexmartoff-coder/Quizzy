import random

# === БОЛЬШОЙ ПУЛ ВОПРОСОВ ===
# Ниже представлен структурированный пул вопросов для квиза.
# В реальной системе этот список может содержать тысячи вопросов.

QUESTIONS_POOL = [
    # Тема: История Apple
    {"id": 1, "question": "В каком году была основана компания Apple?", "options": ["1970", "1976", "1980", "1984"], "correct_index": 1, "explanation": "Apple была основана 1 апреля 1976 года Стивом Джобсом, Стивом Возняком и Рональдом Уэйном."},
    {"id": 2, "question": "Как звали третьего сооснователя Apple, который продал свою долю за 800 долларов?", "options": ["Рональд Уэйн", "Тим Кук", "Джон Скалли", "Майк Марккула"], "correct_index": 0, "explanation": "Рональд Уэйн владел 10% акций Apple, но продал их через две недели после основания."},
    {"id": 3, "question": "Как назывался первый компьютер Apple?", "options": ["Apple I", "Apple II", "Macintosh", "Lisa"], "correct_index": 0, "explanation": "Apple I был разработан и вручную собран Стивом Возняком в 1976 году."},

    # Тема: iPhone
    {"id": 10, "question": "Какой iPhone первым получил поддержку 4G (LTE)?", "options": ["iPhone 4", "iPhone 4S", "iPhone 5", "iPhone 5S"], "correct_index": 2, "explanation": "iPhone 5, выпущенный в 2012 году, стал первым iPhone с поддержкой сетей LTE."},
    {"id": 11, "question": "В какой процессе создания первого iPhone был продан первый официальный iPhone?", "options": ["США", "Великобритания", "Китай", "Германия"], "correct_index": 0, "explanation": "Продажи первого iPhone начались в США 29 июня 2007 года."},
    {"id": 12, "question": "Какое кодовое название носил проект по созданию первого iPhone?", "options": ["Project Purple", "Project Galaxy", "Project X", "Project Titan"], "correct_index": 0, "explanation": "Проект iPhone разрабатывался под строжайшим секретом и назывался Project Purple."},

    # Тема: iOS
    {"id": 20, "question": "Как назывался магазин приложений до появления App Store?", "options": ["iTunes Store", "Web Apps", "Cydia", "Installer"], "correct_index": 1, "explanation": "До появления SDK и App Store Стив Джобс настаивал на использовании веб-приложений на базе Safari."},
    {"id": 21, "question": "В какой версии iOS появился центр управления (Control Center)?", "options": ["iOS 6", "iOS 7", "iOS 8", "iOS 9"], "correct_index": 1, "explanation": "iOS 7 принесла радикальный редизайн и функцию центра управления."},

    # Тема: Технологии
    {"id": 30, "question": "Что означает буква 'i' в названии iMac (и позже iPhone)?", "options": ["Internet", "Individual", "Instruct", "Все вышеперечисленное"], "correct_index": 3, "explanation": "При представлении iMac в 1998 году Джобс сказал, что i означает интернет, индивидуальность, обучение (instruct), информирование и вдохновение."},
    {"id": 31, "question": "Какая компания производит процессоры серии A для Apple?", "options": ["Intel", "Qualcomm", "TSMC", "Nvidia"], "correct_index": 2, "explanation": "TSMC является основным производителем чипов Apple Silicon."},

    # Тема: География и Apple
    {"id": 40, "question": "Где находится штаб-квартира Apple (Apple Park)?", "options": ["Сан-Франциско", "Купертино", "Пало-Альто", "Сан-Хосе"], "correct_index": 1, "explanation": "Apple Park расположен в Купертино, штат Калифорния."},
    {"id": 41, "question": "В честь какого города названа macOS 10.14?", "options": ["Sierra", "High Sierra", "Mojave", "Catalina"], "correct_index": 2, "explanation": "Mojave названа в честь пустыни Мохаве в Калифорнии."},
]

# Генерируем дополнительные вопросы программно для объема
for i in range(50, 150):
    theme_id = i // 10
    QUESTIONS_POOL.append({
        "id": i,
        "question": f"Вопрос №{i} из категории {theme_id}. Каков правильный ответ?",
        "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
        "correct_index": random.randint(0, 3),
        "explanation": f"Это объяснение для вопроса №{i}. Всегда полезно знать детали!"
    })
