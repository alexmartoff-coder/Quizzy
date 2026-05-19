import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import SPREADSHEET_ID

# Путь к файлу с учетными данными Service Account
CREDENTIALS_FILE = "credentials.json"

# SCOPES для доступа к Google Sheets и Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def get_service():
    """Авторизация и получение сервиса Google Sheets API."""
    if not os.path.exists(CREDENTIALS_FILE):
        logging.error(f"Файл {CREDENTIALS_FILE} не найден!")
        return None, None

    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    return sheets_service, drive_service

async def export_to_google_sheets(data):
    """
    Экспортирует данные в Google Таблицу.
    Если SPREADSHEET_ID нет в конфиге, создает новую таблицу.
    """
    sheets_service, drive_service = get_service()
    if not sheets_service:
        return None, "Ошибка авторизации Google API (credentials.json?)"

    global SPREADSHEET_ID
    spreadsheet_id = SPREADSHEET_ID

    try:
        # 1. Если ID нет, создаем новую таблицу
        if not spreadsheet_id:
            spreadsheet = {
                'properties': {
                    'title': 'iPhone 17 Giveaway - Users Data'
                }
            }
            spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            # Сохраняем в .env (попытка записи)
            try:
                with open(".env", "a") as f:
                    f.write(f"\nSPREADSHEET_ID={spreadsheet_id}")
                logging.info(f"Создана новая таблица: {spreadsheet_id}")
            except Exception as e:
                logging.error(f"Не удалось записать SPREADSHEET_ID в .env: {e}")

        # 2. Подготовка заголовков и данных
        headers = ["Telegram ID", "Username", "First Name", "Билеты (всего)", "Квиз (баллы)", "Дата регистрации", "Последняя активность"]
        values = [headers]
        for row in data:
            # Превращаем None в пустые строки для красоты
            values.append([str(item) if item is not None else "" for item in row])

        # 3. Запись данных (очищаем и записываем заново для простоты обновления структуры)
        body = {
            'values': values
        }

        # Очищаем лист перед записью
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1:Z10000"
        ).execute()

        # Записываем новые данные
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Форматирование заголовка (опционально, жирный шрифт)
        requests = [
            {
                "repeatCell": {
                    "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {"bold": True},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
                }
            }
        ]
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        # Возвращаем ссылку на таблицу
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}", None

    except HttpError as err:
        logging.error(f"Ошибка Google API: {err}")
        return None, f"Ошибка Google Sheets API: {err.reason}"
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        return None, f"Ошибка: {str(e)}"
