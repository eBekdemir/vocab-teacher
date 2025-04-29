import os
from dotenv import load_dotenv
from datetime import time
import pytz

load_dotenv()

os.environ['PYTHONIOENCODING'] = 'utf-8'

DB_PATH = os.getenv("DB_PATH", "database/theDataBase.db")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API = os.getenv("OPENROUTER_API_KEY")

DAILY_ESSAYS_TIME = time(hour=19, minute=0, second=0, tzinfo=pytz.utc)

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/bot.log")
if not os.path.exists(os.path.dirname(LOG_FILE_PATH)):
    os.makedirs(os.path.dirname(LOG_FILE_PATH))

AI_MODEL = os.getenv("AI_MODEL").split(":,:")[0] if os.getenv("AI_MODEL") else None
if AI_MODEL is None:
    raise ValueError("AI_MODEL environment variable is not set. Please set it to the desired AI model name.")

RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))
