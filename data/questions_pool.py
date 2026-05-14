import random

# === БОЛЬШОЙ ПУЛ ВОПРОСОВ ===
# Пул из 40+ качественных вопросов про Apple и iPhone на русском языке.

QUESTIONS_POOL = [
    # Тема: История Apple
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
        "explanation": "Apple I был первым продуктом компании, выпущенным в 1976 году."
    },
    {
        "question": "В каком году Стив Джобс представил первый iPhone?",
        "options": ["2005", "2006", "2007", "2008"],
        "correct_index": 2,
        "explanation": "Первый iPhone был представлен 9 января 2007 года на Macworld."
    },
    {
        "question": "Кто стал генеральным директором Apple после смерти Стива Джобса?",
        "options": ["Тим Кук", "Джони Айв", "Фил Шиллер", "Эдди Кью"],
        "correct_index": 0,
        "explanation": "Тим Кук официально стал CEO в августе 2011 года."
    },
    {
        "question": "Какую компанию купила Apple в 1997 году, что привело к возвращению Стива Джобса?",
        "options": ["NeXT", "Pixar", "Microsoft", "Intel"],
        "correct_index": 0,
        "explanation": "Покупка NeXT позволила Apple использовать их ОС как основу для macOS."
    },

    # Тема: Модели iPhone
    {
        "question": "Какой iPhone первым получил поддержку сетей 3G?",
        "options": ["iPhone Original", "iPhone 3G", "iPhone 3GS", "iPhone 4"],
        "correct_index": 1,
        "explanation": "Вторая модель iPhone получила название 3G именно из-за поддержки сетей третьего поколения."
    },
    {
        "question": "Какой iPhone первым получил сканер отпечатков пальцев Touch ID?",
        "options": ["iPhone 5", "iPhone 5c", "iPhone 5s", "iPhone 6"],
        "correct_index": 2,
        "explanation": "Touch ID дебютировал в iPhone 5s в 2013 году."
    },
    {
        "question": "В какой модели iPhone впервые убрали кнопку 'Домой' и перешли на Face ID?",
        "options": ["iPhone 7", "iPhone 8", "iPhone X", "iPhone XR"],
        "correct_index": 2,
        "explanation": "iPhone X стал первым безрамочным iPhone с Face ID."
    },
    {
        "question": "Какая модель iPhone была представлена как 'бюджетная' версия iPhone 5?",
        "options": ["iPhone 5s", "iPhone 5c", "iPhone SE", "iPhone 4s"],
        "correct_index": 1,
        "explanation": "iPhone 5c имел пластиковый корпус и был доступен в нескольких цветах."
    },
    {
        "question": "Какой iPhone первым получил три камеры на задней панели?",
        "options": ["iPhone X", "iPhone Xs Max", "iPhone 11 Pro", "iPhone 12 Pro"],
        "correct_index": 2,
        "explanation": "iPhone 11 Pro и 11 Pro Max стали первыми с системой из трех камер."
    },
    {
        "question": "В каком году вышел первый iPhone SE?",
        "options": ["2015", "2016", "2017", "2018"],
        "correct_index": 1,
        "explanation": "Первый iPhone SE (в корпусе 5s) был представлен в марте 2016 года."
    },

    # Тема: Технологии и компоненты
    {
        "question": "Как называется технология дисплея с высокой плотностью пикселей, представленная в iPhone 4?",
        "options": ["Super AMOLED", "Retina", "Liquid Crystal", "OLED"],
        "correct_index": 1,
        "explanation": "Retina-дисплей стал одной из главных фишек iPhone 4."
    },
    {
        "question": "Как называется разъем для зарядки, который использовался в iPhone с 2012 по 2023 год?",
        "options": ["30-pin", "Micro-USB", "Lightning", "USB-C"],
        "correct_index": 2,
        "explanation": "Lightning был представлен в iPhone 5 и использовался до выхода iPhone 15."
    },
    {
        "question": "Какой процессор используется в iPhone 15 Pro?",
        "options": ["A16 Bionic", "A17 Pro", "M1", "M2"],
        "correct_index": 1,
        "explanation": "iPhone 15 Pro получил мощный чип A17 Pro."
    },
    {
        "question": "Как называется фирменный голосовой помощник Apple?",
        "options": ["Alexa", "Cortana", "Siri", "Alice"],
        "correct_index": 2,
        "explanation": "Siri была интегрирована в iOS, начиная с iPhone 4S."
    },
    {
        "question": "Какая технология позволяет оплачивать покупки с помощью iPhone?",
        "options": ["Apple Pay", "iPay", "QuickPay", "Contactless"],
        "correct_index": 0,
        "explanation": "Apple Pay использует NFC для бесконтактных платежей."
    },

    # Тема: iOS и ПО
    {
        "question": "Как называлась операционная система iPhone до того, как её переименовали в iOS?",
        "options": ["Mac OS X", "iPhone OS", "Mobile OS", "Apple OS"],
        "correct_index": 1,
        "explanation": "До 2010 года система называлась iPhone OS."
    },
    {
        "question": "В какой версии iOS появился магазин приложений App Store?",
        "options": ["iOS 1", "iOS 2", "iOS 3", "iOS 4"],
        "correct_index": 1,
        "explanation": "App Store появился в июле 2008 года вместе с iPhone 3G и iOS 2."
    },
    {
        "question": "Как называется функция для быстрой передачи файлов между устройствами Apple?",
        "options": ["BlueShare", "iTransfer", "AirDrop", "QuickSend"],
        "correct_index": 2,
        "explanation": "AirDrop позволяет передавать файлы по Wi-Fi и Bluetooth."
    },
    {
        "question": "Как называется браузер по умолчанию в iOS?",
        "options": ["Chrome", "Opera", "Safari", "Firefox"],
        "correct_index": 2,
        "explanation": "Safari является стандартным браузером на всех устройствах Apple."
    },

    # Тема: Дизайн и Культура
    {
        "question": "Кто был главным дизайнером большинства продуктов Apple до 2019 года?",
        "options": ["Тим Кук", "Джони Айв", "Стив Возняк", "Крейг Федериги"],
        "correct_index": 1,
        "explanation": "Джони Айв спроектировал облик iMac, iPod, iPhone и iPad."
    },
    {
        "question": "Как называется новая штаб-квартира Apple в Купертино?",
        "options": ["Apple Center", "Infinite Loop", "Apple Park", "Apple Square"],
        "correct_index": 2,
        "explanation": "Apple Park — это огромное кольцеобразное здание в Купертино."
    },
    {
        "question": "В честь какого сорта яблок была названа линейка компьютеров Macintosh?",
        "options": ["Golden Delicious", "McIntosh", "Granny Smith", "Fuji"],
        "correct_index": 1,
        "explanation": "Джефф Раскин назвал проект в честь своего любимого сорта яблок (с небольшим изменением в написании)."
    },
    {
        "question": "Какое известное рекламное видео Apple представило компьютер Macintosh в 1984 году?",
        "options": ["The Future", "Think Different", "1984", "New World"],
        "correct_index": 2,
        "explanation": "Рекламный ролик '1984', снятый Ридли Скоттом, стал культовым."
    },

    # Тема: Другие продукты
    {
        "question": "Как назывался музыкальный плеер Apple, совершивший революцию в индустрии?",
        "options": ["iSound", "iPlayer", "iPod", "Walkman"],
        "correct_index": 2,
        "explanation": "Первый iPod был представлен в 2001 году."
    },
    {
        "question": "В каком году были представлены первые наушники AirPods?",
        "options": ["2014", "2015", "2016", "2017"],
        "correct_index": 2,
        "explanation": "AirPods были анонсированы вместе с iPhone 7 в 2016 году."
    },
    {
        "question": "Как называются умные часы от Apple?",
        "options": ["iWatch", "Apple Watch", "SmartWatch", "Apple Clock"],
        "correct_index": 1,
        "explanation": "Первые Apple Watch поступили в продажу в 2015 году."
    },
    {
        "question": "Какое устройство Apple представило в 2010 году как нечто среднее между смартфоном и ноутбуком?",
        "options": ["iPad", "MacBook Air", "iPhone XL", "iTab"],
        "correct_index": 0,
        "explanation": "Первый iPad был представлен в январе 2010 года."
    },

    # Дополнительные вопросы для объема (до 40+)
    {
        "question": "Какой материал использовался в корпусе iPhone 4 и 4S с обеих сторон?",
        "options": ["Пластик", "Алюминий", "Стекло", "Сталь"],
        "correct_index": 2,
        "explanation": "iPhone 4 имел стеклянные переднюю и заднюю панели."
    },
    {
        "question": "Как называлась первая мышь Apple с сенсорной поверхностью?",
        "options": ["Magic Mouse", "Mighty Mouse", "iMouse", "Touch Mouse"],
        "correct_index": 0,
        "explanation": "Magic Mouse была представлена в 2009 году."
    },
    {
        "question": "Какое разрешение видео впервые стало доступно в iPhone 4S?",
        "options": ["480p", "720p", "1080p", "4K"],
        "correct_index": 2,
        "explanation": "iPhone 4S стал первым iPhone, умеющим снимать Full HD видео."
    },
    {
        "question": "Как называется технология дисплея в iPhone 14 Pro, заменяющая 'челку'?",
        "options": ["Dynamic Island", "Magic Hole", "Smart Notch", "Active Area"],
        "correct_index": 0,
        "explanation": "Dynamic Island стал интерактивным вырезом в экране."
    },
    {
        "question": "В каком году Apple представила свои собственные процессоры M1 для Mac?",
        "options": ["2018", "2019", "2020", "2021"],
        "correct_index": 2,
        "explanation": "Переход на Apple Silicon (M1) начался в конце 2020 года."
    },
    {
        "question": "Как называется приложение для поиска потерянных устройств Apple?",
        "options": ["Find Me", "iSearch", "Локатор (Find My)", "WhereIsMyiPhone"],
        "correct_index": 2,
        "explanation": "Приложение 'Локатор' объединило сервисы 'Найти iPhone' и 'Найти друзей'."
    },
    {
        "question": "Какой iPhone первым получил корпус из титана?",
        "options": ["iPhone 14 Pro", "iPhone 15 Pro", "iPhone 13 Pro", "iPhone 12 Pro"],
        "correct_index": 1,
        "explanation": "Линейка iPhone 15 Pro получила рамку из титана аэрокосмического класса."
    },
    {
        "question": "Как называется магазин контента для Mac и iPhone, запущенный еще до App Store?",
        "options": ["Music Store", "iTunes Store", "Apple Store", "Content Store"],
        "correct_index": 1,
        "explanation": "iTunes Music Store был запущен в 2003 году."
    },
    {
        "question": "Кто из основателей Apple разработал схему Apple I и Apple II?",
        "options": ["Стив Джобс", "Стив Возняк", "Рональд Уэйн", "Майк Марккула"],
        "correct_index": 1,
        "explanation": "Стив Возняк (Воз) был техническим гением, создавшим первые компьютеры Apple."
    },
    {
        "question": "Как называется сервис Apple для хранения данных в облаке?",
        "options": ["iDrive", "Apple Cloud", "iCloud", "MobileMe"],
        "correct_index": 2,
        "explanation": "iCloud был представлен в 2011 году как замена MobileMe."
    },
    {
        "question": "Какое кодовое имя носила первая версия Mac OS X (10.0)?",
        "options": ["Puma", "Jaguar", "Cheetah", "Tiger"],
        "correct_index": 2,
        "explanation": "Mac OS X 10.0 называлась Cheetah (Гепард)."
    },
    {
        "question": "В какой модели iPhone впервые появилась поддержка беспроводной зарядки?",
        "options": ["iPhone 7", "iPhone 8 / X", "iPhone Xs", "iPhone 11"],
        "correct_index": 1,
        "explanation": "iPhone 8, 8 Plus и iPhone X стали первыми с поддержкой стандарта Qi."
    }
]
