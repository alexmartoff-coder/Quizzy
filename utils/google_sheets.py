import os
import json
import logging
import aiosqlite
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CREDS_JSON, SPREADSHEET_ID
from database.db import DB_PATH

# SCOPES для доступа к Google Sheets и Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

def get_service():
    """Авторизация и получение сервиса Google Sheets API из переменной окружения."""
    if not GOOGLE_CREDS_JSON:
        logging.error("Переменная GOOGLE_CREDS_JSON не установлена!")
        return None, None, None

    try:
        info = json.loads(GOOGLE_CREDS_JSON)
        client_email = info.get("client_email")
        credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        # cache_discovery=False подавляет предупреждения о file_cache
        sheets_service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
        return sheets_service, drive_service, client_email
    except Exception as e:
        logging.error(f"Ошибка парсинга GOOGLE_CREDS_JSON: {e}")
        return None, None, None

async def export_to_google_sheets(data):
    """
    Экспортирует данные в Google Таблицу по фиксированному ID.
    Использует логику обновления существующих строк и добавления новых.
    """
    sheets_service, drive_service, client_email = get_service()
    if not sheets_service:
        return None, "Ошибка авторизации Google API (проверьте GOOGLE_CREDS_JSON)"

    spreadsheet_id = SPREADSHEET_ID

    try:
        # 1. Читаем текущие данные из таблицы, чтобы понять, кто уже есть
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A:A"  # Читаем только первый столбец (Telegram ID)
        ).execute()

        current_rows = result.get('values', [])
        # Создаем мапу {user_id: row_index} (row_index 1-based)
        existing_users = {}
        for idx, row in enumerate(current_rows):
            if row:
                existing_users[row[0]] = idx + 1

        # 2. Подготовка заголовков (если таблица пустая)
        if not current_rows:
            headers = ["Telegram ID", "Username", "First Name", "Билеты (всего)", "Квиз (баллы)", "Дата регистрации", "Последняя активность"]
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="RAW",
                body={'values': [headers]}
            ).execute()
            # Форматирование заголовка
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [{
                        "repeatCell": {
                            "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}},
                            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
                        }
                    }]
                }
            ).execute()

        # 3. Распределяем данные на обновление и добавление
        rows_to_update = [] # List of {'range': ..., 'values': ...}
        rows_to_append = [] # List of lists

        for user_data in data:
            uid = str(user_data[0])
            formatted_row = [str(item) if item is not None else "" for item in user_data]

            if uid in existing_users:
                row_idx = existing_users[uid]
                rows_to_update.append({
                    'range': f"Sheet1!A{row_idx}:G{row_idx}",
                    'values': [formatted_row]
                })
            else:
                rows_to_append.append(formatted_row)

        # 4. Выполняем обновления (batchUpdate для скорости)
        if rows_to_update:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': rows_to_update
                }
            ).execute()

        # 5. Выполняем добавления
        if rows_to_append:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="RAW",
                body={'values': rows_to_append}
            ).execute()

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}", None

    except HttpError as err:
        if err.resp.status == 403:
            return None, (
                f"Ошибка 403: Нет доступа к таблице.\n\n"
                f"ID Таблицы: <code>{spreadsheet_id}</code>\n"
                f"Необходимо добавить этот email в список редакторов:\n"
                f"<code>{client_email}</code>"
            )
        logging.error(f"Ошибка Google API: {err}")
        return None, f"Ошибка API: {err.reason}"
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        return None, f"Ошибка: {str(e)}"
