import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

CHANNEL_ID = "@mozgo_boy"
OWNER_ID = int(os.getenv("OWNER_ID", "228592391"))

TICKET_LIMIT = 3500
