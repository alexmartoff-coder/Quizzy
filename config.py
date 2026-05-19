import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

CHANNEL_ID = "@mozgo_boy"
OWNER_ID = int(os.getenv("OWNER_ID", "228592391"))
YOOKASSA_PROVIDER_TOKEN = os.getenv("YOOKASSA_PROVIDER_TOKEN")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

TICKET_LIMIT = 3500
