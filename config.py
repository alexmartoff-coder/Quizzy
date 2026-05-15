import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "YOUR_PROVIDER_TOKEN")
CHANNEL_ID = "@mozgo_boy"
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

TICKET_LIMIT = 2500
COLLECTION_DEADLINE = datetime(2026, 4, 10, tzinfo=timezone.utc)

QUIZ_PRICE = 99  # in RUB
