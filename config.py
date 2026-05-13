import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "YOUR_PROVIDER_TOKEN")
CHANNEL_ID = "@mozgo_boy"

TICKET_LIMIT = 2500

QUIZ_PRICE = 99  # in RUB
