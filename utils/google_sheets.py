import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CREDS_JSON, SPREADSHEET_ID

# SCOPES для доступа к Google Sheets и Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

SHEET_NAME = "Данные"

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

async def ensure_sheet_exists(sheets_service, spreadsheet_id):
    """Проверяет существование листа SHEET_NAME и создает его, если он отсутствует."""
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_titles = [s.get('properties', {}).get('title') for s in sheets]

        headers = ["Telegram ID", "Username", "First Name", "Билеты (всего)", "Квиз (баллы)", "Дата регистрации", "Последняя активность"]

        if SHEET_NAME not in sheet_titles:
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': SHEET_NAME
                            }
                        }
                    }
                ]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

            # Сразу записываем заголовки
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{SHEET_NAME}'!A1",
                valueInputOption="RAW",
                body={'values': [headers]}
            ).execute()

            # Форматирование заголовка
            res = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            new_sheet_id = next(s['properties']['sheetId'] for s in res['sheets'] if s['properties']['title'] == SHEET_NAME)

            format_body = {
                "requests": [{
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
                    }
                }]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=format_body).execute()
        return True
    except HttpError as e:
        logging.error(f"Error ensuring sheet exists: {e}")
        raise e

async def export_to_google_sheets(data):
    """
    Экспортирует данные в Google Таблицу по фиксированному ID.
    Использует логику обновления существующих строк и добавления новых на листе SHEET_NAME.
    """
    sheets_service, drive_service, client_email = get_service()
    if not sheets_service:
        return None, "Ошибка авторизации Google API (проверьте GOOGLE_CREDS_JSON)"

    spreadsheet_id = SPREADSHEET_ID

    try:
        # Убеждаемся, что лист существует
        await ensure_sheet_exists(sheets_service, spreadsheet_id)

        # 1. Читаем все данные с листа для точного сопоставления
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{SHEET_NAME}'!A:G"
        ).execute()

        current_rows = result.get('values', [])
        existing_users = {}
        for idx, row in enumerate(current_rows):
            if row and len(row) > 0 and row[0].isdigit():
                existing_users[row[0]] = idx + 1 # row_index 1-based

        # 2. Распределяем данные
        rows_to_update = []
        rows_to_append = []

        for user_data in data:
            uid = str(user_data[0])
            formatted_row = [str(item) if item is not None else "" for item in user_data]

            if uid in existing_users:
                row_idx = existing_users[uid]
                rows_to_update.append({
                    'range': f"'{SHEET_NAME}'!A{row_idx}:G{row_idx}",
                    'values': [formatted_row]
                })
            else:
                rows_to_append.append(formatted_row)

        # 3. Выполняем обновления (batchUpdate для оптимизации)
        if rows_to_update:
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': rows_to_update
                }
            ).execute()

        # 4. Выполняем добавления
        if rows_to_append:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"'{SHEET_NAME}'!A1",
                valueInputOption="RAW",
                body={'values': rows_to_append}
            ).execute()

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}", None

    except HttpError as err:
        if err.resp.status == 403:
            return None, (
                f"Ошибка 403: Нет доступа к таблице.\n\n"
                f"ID: <code>{spreadsheet_id}</code>\n"
                f"Добавьте этот email в редакторы:\n"
                f"<code>{client_email}</code>"
            )
        logging.error(f"Ошибка Google API: {err}")
        return None, f"Ошибка API: {err.reason}"
    except Exception as e:
        logging.error(f"Ошибка экспорта: {e}")
        return None, f"Ошибка: {str(e)}"
