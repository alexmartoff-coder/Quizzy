import random

# === БОЛЬШОЙ ПУЛ ВОПРОСОВ ===
# Пул из 40+ качественных вопросов про Apple и iPhone на русском языке.
# Разделены по темам: История, Модели, Технологии, Дизайн, iOS.

QUESTIONS_POOL = [
    # --- История Apple ---
    {
        "question": "В каком году Стив Джобс, Стив Возняк и Рональд Уэйн основали Apple?",
        "options": ["1974", "1976", "1978", "1980"],
        "correct_index": 1,
        "explanation": "Apple была основана 1 апреля 1976 года."
    },
    {
        "question": "Как назывался первый компьютер, выпущенный компанией Apple?",
        "options": ["Apple I", "Apple II", "Macintosh", "Lisa"],
        "correct_index": 0,
        "explanation": "Apple I был первым продуктом компании, созданным Стивом Возняком."
    },
    {
        "question": "Какую компанию купила Apple в 1997 году, что привело к возвращению Стива Джобса?",
        "options": ["NeXT", "Pixar", "Microsoft", "Intel"],
        "correct_index": 0,
        "explanation": "Покупка NeXT позволила использовать их наработки для создания macOS."
    },
    {
        "question": "Кто стал генеральным директором Apple после смерти Стива Джобса в 2011 году?",
        "options": ["Тим Кук", "Джони Айв", "Фил Шиллер", "Эдди Кью"],
        "correct_index": 0,
        "explanation": "Тим Кук занял пост CEO в августе 2011 года."
    },
    {
        "question": "В каком году Стив Джобс представил первый iPhone на конференции Macworld?",
        "options": ["2005", "2006", "2007", "2008"],
        "correct_index": 2,
        "explanation": "Знаменитая презентация состоялась 9 января 2007 года."
    },

    # --- Модели iPhone ---
    {
        "question": "Какой iPhone первым получил поддержку сетей 3G?",
        "options": ["iPhone Original", "iPhone 3G", "iPhone 3GS", "iPhone 4"],
        "correct_index": 1,
        "explanation": "Вторая модель iPhone получила название 3G именно за поддержку новых сетей."
    },
    {
        "question": "Какой iPhone первым получил сканер Touch ID?",
        "options": ["iPhone 5", "iPhone 5s", "iPhone 6", "iPhone 4s"],
        "correct_index": 1,
        "explanation": "Touch ID дебютировал в iPhone 5s в 2013 году."
    },
    {
        "question": "В какой модели iPhone впервые убрали разъем для наушников 3.5 мм?",
        "options": ["iPhone 6s", "iPhone 7", "iPhone 8", "iPhone X"],
        "correct_index": 1,
        "explanation": "iPhone 7 стал первым смартфоном Apple без аудиоразъема."
    },
    {
        "question": "Какой iPhone стал первым с OLED-дисплеем и без кнопки Домой?",
        "options": ["iPhone 8", "iPhone X", "iPhone Xs", "iPhone 11"],
        "correct_index": 1,
        "explanation": "Юбилейный iPhone X радикально изменил дизайн линейки."
    },
    {
        "question": "Какой iPhone первым получил корпус из титана?",
        "options": ["iPhone 14 Pro", "iPhone 15 Pro", "iPhone 13 Pro", "iPhone 12 Pro"],
        "correct_index": 1,
        "explanation": "Линейка 15 Pro получила рамку из авиационного титана."
    },
    {
        "question": "Какая модель iPhone имела пластиковый корпус и выпускалась в ярких цветах?",
        "options": ["iPhone 5", "iPhone 5c", "iPhone 5s", "iPhone SE"],
        "correct_index": 1,
        "explanation": "iPhone 5c позиционировался как более доступная и молодежная модель."
    },

    # --- Технологии и Компоненты ---
    {
        "question": "Как называется технология дисплея с высокой плотностью пикселей, представленная в iPhone 4?",
        "options": ["Super AMOLED", "Liquid Crystal", "Retina", "True Tone"],
        "correct_index": 2,
        "explanation": "Retina-дисплей сделал изображение невероятно четким."
    },
    {
        "question": "Как называется фирменный процессор Apple, дебютировавший в iPhone 4?",
        "options": ["Apple A4", "Apple M1", "Apple i1", "Apple X1"],
        "correct_index": 0,
        "explanation": "A4 стал первым процессором собственной разработки Apple для iPhone."
    },
    {
        "question": "Как называется голосовой помощник, появившийся в iPhone 4S?",
        "options": ["Alexa", "Siri", "Alice", "Cortana"],
        "correct_index": 1,
        "explanation": "Siri стала одной из ключевых особенностей iPhone 4S."
    },
    {
        "question": "Какой разъем использовался в iPhone до перехода на Lightning в 2012 году?",
        "options": ["Micro-USB", "Mini-USB", "30-pin connector", "USB-C"],
        "correct_index": 2,
        "explanation": "Старый широкий разъем использовался со времен первых iPod."
    },
    {
        "question": "Как называется технология распознавания лица в iPhone?",
        "options": ["Face Scan", "Look ID", "Face ID", "Bio Unlock"],
        "correct_index": 2,
        "explanation": "Face ID пришла на смену Touch ID в iPhone X."
    },
    {
        "question": "Какая технология позволяет iPhone заряжаться без проводов?",
        "options": ["AirPower", "Qi", "NFC", "MagSafe Charge"],
        "correct_index": 1,
        "explanation": "Apple использует общемировой стандарт беспроводной зарядки Qi."
    },

    # --- Дизайн и ПО ---
    {
        "question": "Как называлась операционная система iPhone до 2010 года?",
        "options": ["Mac OS Mobile", "iPhone OS", "Apple OS", "iOS Lite"],
        "correct_index": 1,
        "explanation": "Название iOS было принято только во время выхода iPad."
    },
    {
        "question": "В какой версии iOS появился магазин приложений App Store?",
        "options": ["iOS 1", "iOS 2", "iOS 3", "iOS 4"],
        "correct_index": 1,
        "explanation": "App Store был представлен вместе с iPhone 3G."
    },
    {
        "question": "Как называется функция быстрой передачи файлов между устройствами Apple?",
        "options": ["iDrop", "AirDrop", "BlueDrop", "QuickShare"],
        "correct_index": 1,
        "explanation": "AirDrop использует Wi-Fi и Bluetooth для мгновенной передачи."
    },
    {
        "question": "Кто был главным дизайнером Apple, создавшим облик iMac, iPod и iPhone?",
        "options": ["Стив Возняк", "Тим Кук", "Джони Айв", "Крейг Федериги"],
        "correct_index": 2,
        "explanation": "Сэр Джонатан Айв определял дизайн Apple более 20 лет."
    },
    {
        "question": "Как называется браузер по умолчанию на всех устройствах Apple?",
        "options": ["Chrome", "Safari", "Opera", "iSearch"],
        "correct_index": 1,
        "explanation": "Safari построен на движке WebKit и оптимизирован для Apple."
    },

    # --- Прочее ---
    {
        "question": "Какое устройство Apple представило в 2010 году как 'третью категорию' между смартфоном и ноутбуком?",
        "options": ["Apple Watch", "iPad", "MacBook Air", "Apple TV"],
        "correct_index": 1,
        "explanation": "Первый iPad перевернул рынок планшетных компьютеров."
    },
    {
        "question": "Как называется подписочный сервис Apple с играми?",
        "options": ["Apple Games", "Apple Play", "Apple Arcade", "iGame"],
        "correct_index": 2,
        "explanation": "Apple Arcade предлагает доступ к сотням игр без рекламы."
    },
    {
        "question": "Какое животное изображено на логотипе языка программирования Swift, созданного Apple?",
        "options": ["Гепард", "Орел", "Стриж", "Дельфин"],
        "correct_index": 2,
        "explanation": "Swift переводится как 'Стриж', что подчеркивает скорость языка."
    },
    {
        "question": "Какое кодовое имя носил проект по созданию первого iPhone?",
        "options": ["Project X", "Project Titan", "Project Purple", "Project Galaxy"],
        "correct_index": 2,
        "explanation": "Project Purple был одним из самых секретных в истории компании."
    },
    {
        "question": "В каком году были представлены первые беспроводные наушники AirPods?",
        "options": ["2015", "2016", "2017", "2018"],
        "correct_index": 1,
        "explanation": "AirPods были анонсированы в сентябре 2016 года."
    },
    {
        "question": "Какой материал использовался в корпусе iPhone 4 с обеих сторон?",
        "options": ["Пластик", "Алюминий", "Стекло", "Керамика"],
        "correct_index": 2,
        "explanation": "iPhone 4 имел стеклянный 'сэндвич-дизайн' со стальной рамкой."
    },
    {
        "question": "Как называется приложение для управления умным домом от Apple?",
        "options": ["iHome", "SmartHouse", "Дом (Home)", "Apple Link"],
        "correct_index": 2,
        "explanation": "Приложение 'Дом' объединяет все устройства HomeKit."
    },
    {
        "question": "Как называется функция iPhone, позволяющая создавать анимированные эмодзи?",
        "options": ["LiveEmoji", "Animoji", "FaceMoji", "iAnim"],
        "correct_index": 1,
        "explanation": "Animoji используют систему камер Face ID для захвата мимики."
    },
    {
        "question": "В честь какого сорта яблок назван компьютер Macintosh?",
        "options": ["Golden", "Granny Smith", "McIntosh", "Fuji"],
        "correct_index": 2,
        "explanation": "Джефф Раскин назвал проект в честь любимого сорта яблок."
    },
    {
        "question": "Как называется технология дисплея в iPhone 14 Pro, заменившая 'челку'?",
        "options": ["Smart Notch", "Magic Island", "Dynamic Island", "Active Area"],
        "correct_index": 2,
        "explanation": "Dynamic Island стал интерактивным элементом интерфейса."
    },
    {
        "question": "Какое разрешение видео впервые стало доступно в iPhone 4S?",
        "options": ["720p", "1080p (Full HD)", "4K", "480p"],
        "correct_index": 1,
        "explanation": "iPhone 4S стал первым iPhone с записью 1080p видео."
    },
    {
        "question": "Как называлась первая версия операционной системы для Apple Watch?",
        "options": ["iOS Watch", "watchOS", "ClockOS", "WristOS"],
        "correct_index": 1,
        "explanation": "watchOS была разработана специально для носимых устройств."
    },
    {
        "question": "Какой iPhone первым получил три камеры?",
        "options": ["iPhone X", "iPhone Xs", "iPhone 11 Pro", "iPhone 12 Pro"],
        "correct_index": 2,
        "explanation": "Линейка 11 Pro ввела стандарт трехкамерной системы."
    },
    {
        "question": "Как называется сервис Apple для хранения файлов и фото в облаке?",
        "options": ["iDrive", "AppleCloud", "iCloud", "MobileMe"],
        "correct_index": 2,
        "explanation": "iCloud объединяет все устройства пользователя в единую экосистему."
    },
    {
        "question": "Кто из основателей Apple вручную собрал первые платы Apple I?",
        "options": ["Стив Джобс", "Стив Возняк", "Рональд Уэйн", "Майк Марккула"],
        "correct_index": 1,
        "explanation": "Стив 'Воз' Возняк был техническим мозгом компании на старте."
    },
    {
        "question": "Как называется приложение для поиска потерянных устройств Apple?",
        "options": ["Find My iPhone", "Локатор", "Search Apple", "iTracker"],
        "correct_index": 1,
        "explanation": "Приложение 'Локатор' объединило сервисы поиска устройств и друзей."
    },
    {
        "question": "В каком году Apple перешла на собственные процессоры M1 для компьютеров Mac?",
        "options": ["2018", "2019", "2020", "2021"],
        "correct_index": 2,
        "explanation": "Переход на Apple Silicon начался в ноябре 2020 года."
    },
    {
        "question": "Какое разрешение экрана имел первый iPhone (2007)?",
        "options": ["320x480", "640x960", "480x800", "240x320"],
        "correct_index": 0,
        "explanation": "Для того времени разрешение 320x480 было стандартом высокой четкости."
    }
]
