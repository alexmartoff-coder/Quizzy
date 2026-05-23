import os
import json
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CREDS_JSON, SPREADSHEET_ID

async def export_to_google_sheets(data):
    if not GOOGLE_CREDS_JSON or not SPREADSHEET_ID:
        return None, "Google API credentials or Spreadsheet ID missing"

    try:
        creds_dict = json.loads(GOOGLE_CREDS_JSON)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        sheet = service.spreadsheets()

        # Заголовки
        values = [
            ["Telegram ID", "Username", "Full Name", "Tickets", "Quiz Score", "Registration", "Last Activity"]
        ]

        # Данные
        for row in data:
            values.append(list(row))

        body = {
            'values': values
        }

        # Очистка и запись
        sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range="Данные!A1:Z10000").execute()
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="Данные!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
        return url, None

    except Exception as e:
        logging.error(f"Google Sheets Error: {e}")
        return None, str(e)
