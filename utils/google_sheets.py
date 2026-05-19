import os
import json
import logging
import aiosqlite
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CREDENTIALS, SPREADSHEET_ID
from database.db import DB_PATH

# SCOPES для доступа к Google Sheets и Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

async def get_db_spreadsheet_id():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'spreadsheet_id'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_db_spreadsheet_id(spreadsheet_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('spreadsheet_id', ?)", (spreadsheet_id,))
        await db.commit()

def get_service():
    """Авторизация и получение сервиса Google Sheets API из переменной окружения."""
    if not GOOGLE_CREDENTIALS:
        logging.error("Переменная GOOGLE_CREDENTIALS не установлена!")
        return None, None

    try:
        info = json.loads(GOOGLE_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        return sheets_service, drive_service
    except Exception as e:
        logging.error(f"Ошибка парсинга GOOGLE_CREDENTIALS: {e}")
        return None, None

async def export_to_google_sheets(data):
    """
    Экспортирует данные в Google Таблицу.
    Если SPREADSHEET_ID нет, создает новую таблицу.
    """
    sheets_service, drive_service = get_service()
    if not sheets_service:
        return None, "Ошибка авторизации Google API (проверьте GOOGLE_CREDENTIALS)"

    spreadsheet_id = await get_db_spreadsheet_id() or SPREADSHEET_ID

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

            # Сохраняем в БД для персистентности на Railway
            await set_db_spreadsheet_id(spreadsheet_id)
            logging.info(f"Создана новая таблица: {spreadsheet_id}")

        # 2. Подготовка заголовков и данных
        headers = ["Telegram ID", "Username", "First Name", "Билеты (всего)", "Квиз (баллы)", "Дата регистрации", "Последняя активность"]
        values = [headers]
        for row in data:
            values.append([str(item) if item is not None else "" for item in row])

        # 3. Запись данных
        body = {
            'values': values
        }

        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1:Z10000"
        ).execute()

        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Форматирование заголовка
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

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}", None

    except HttpError as err:
        logging.error(f"Ошибка Google API: {err}")
        return None, f"Ошибка API: {err.reason}"
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        return None, f"Ошибка: {str(e)}"
