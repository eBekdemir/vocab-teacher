import os
from dotenv import load_dotenv
from datetime import time
import pytz

load_dotenv()

os.environ['PYTHONIOENCODING'] = 'utf-8'

DB_PATH = os.getenv("DB_PATH", "theDataBase.db")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
deepseek_r1 = os.getenv("OPENROUTER_DEEPSEEK_R1_API_KEY")

DAILY_ESSAYS_TIME = time(hour=17, minute=41, second=0, tzinfo=pytz.utc)

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/bot.log")
if not os.path.exists(os.path.dirname(LOG_FILE_PATH)):
    os.makedirs(os.path.dirname(LOG_FILE_PATH))