import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "YOUR_PROVIDER_TOKEN")
CHANNEL_ID = "@mozgo_boy"  # Or the actual ID if needed

TICKET_LIMIT = 2500
DEADLINE_DATE = datetime(2026, 4, 10, 23, 59, 59)

QUIZ_PRICE = 99  # in RUB
