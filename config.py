import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

CHANNEL_ID = "@mozgo_boy"
OWNER_ID = int(os.getenv("OWNER_ID", "228592391"))

TICKET_LIMIT = 2500
INITIAL_FAKE_TICKETS = 0
MAX_TICKET_NUMBER = 50000

# Конец сбора билетов: 10 апреля 2026
CONTEST_END_DATE = datetime(2026, 4, 10, 23, 59, 59)

GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
SPREADSHEET_ID = "1dJ2AFECSBqoIJQkzfXPmdxVr8DSWPpuufU_l88mZD-Y"
