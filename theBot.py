import word_scraper as word

### python-telegram-bot==13.15
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue, MessageHandler, Filters
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, NetworkError
from dotenv import load_dotenv

import os
import requests
import logging
import sqlite3
import threading
import urllib3
import pandas as pd

load_dotenv()
os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from win10toast import ToastNotifier
toaster = ToastNotifier()
toaster.show_toast("The Vocabulary Bot", "The Vocabulary Bot has just started!", duration=5, threaded=True)


db_path = 'theDataBase.db'
db_lock = threading.Lock()

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.info("Disabled InsecureRequestWarning from urllib3.")
except Exception as e:
    logger.warning(f"Could not disable InsecureRequestWarning: {e}")


# --- DataBase Functions ---
def init_db():
    with db_lock:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chat_ids (
                        chat_id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        username TEXT,
                        first_reminder INTEGER DEFAULT 1,
                        second_reminder INTEGER DEFAULT 2,
                        third_reminder INTEGER DEFAULT 4,
                        fourth_reminder INTEGER DEFAULT 8,
                        fifth_reminder INTEGER DEFAULT 16
                        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY,
                        word TEXT,
                        definitions TEXT,
                        examples TEXT,
                        turkish_meaning TEXT DEFAULT NULL
                        )''') ### TODO: add turkish meaning
        c.execute('''CREATE TABLE IF NOT EXISTS user_words (
                        id INTEGER PRIMARY KEY,
                        chat_id INTEGER,
                        word_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chat_ids (chat_id),
                        FOREIGN KEY (word_id) REFERENCES words (id)
                        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            chat_id INTEGER,
                            message TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                            )''')
        conn.commit()
        conn.close()
    logger.info("Database initialized.")

def add_word_to_db(wrd: str) -> tuple[int, list[str], list[str]]: # returns word_id
    definitions, examples = word.scrape_the_word(wrd)
    if not definitions and not examples:
        logger.warning(f"No definitions or examples found for word: {word}")
        return None
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO words (word, definitions, examples) VALUES (?, ?, ?)''',
                    (wrd, ';;;'.join(definitions), ';;;'.join(examples)))
        word_id = cursor.lastrowid
        conn.commit()
        conn.close()

    logger.info(f"Word '{wrd}' added to database with ID {word_id}.")
    return word_id, definitions, examples

def get_word_from_db(wrd: str) -> tuple[list[str], list[str]]:
    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT id, definitions, examples FROM words WHERE word = ?''', (wrd,))
            result = cursor.fetchone()
            conn.close()

        if result:
            word_id, definitions, examples = result
            logging.info(f"Retrieved definitions and examples for word '{wrd}' from database.")
            return word_id, definitions.split(';;;'), examples.split(';;;')
        else:
            logging.warning(f"Word '{wrd}' not found in database.")
            return 'NOT IN DATABASE'
    except sqlite3.Error as e: 
        logger.error(f"SQLite error: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Error retrieving a word ({wrd}): {e}")
        return None, None, None

def get_user_words_from_db(chat_id: int) -> list[str]:
    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT word FROM words w
                            JOIN user_words uw ON w.id = uw.word_id
                            WHERE uw.chat_id = ?''', (chat_id,))
            result = cursor.fetchall()
            conn.close()
        if result:
            words = [row[0] for row in result]
            logger.info(f"Retrieved words for chat ID {chat_id} from database.")
            return words
        else:
            logger.warning(f"No words found for chat ID {chat_id}.")
            return []
    except sqlite3.Error as e: 
        logger.error(f"SQLite error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving user words ({chat_id}): {e}")
        return []

def match_user_with_word(chat_id: int, word_id: int) -> bool: 
    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # BUG: Check whether it throws an error or not if the word is already exist in db
            # BUG: If the word is already matched with user, change its created date!!!
            cursor.execute('''INSERT INTO user_words (chat_id, word_id) VALUES (?, ?)''', (chat_id, word_id)) 
            conn.commit()
            conn.close()
        logger.info(f"Matched user with chat ID {chat_id} to word ID {word_id}.")
        return True
    except sqlite3.Error as e: 
        logger.error(f"SQLite error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error matching user with word ({chat_id}, {word_id}): {e}")
        return False

def save_chat_id(user) -> bool:
    chat_id = user.id
    if not chat_id:
        logger.warning("No chat ID found in user object.")
        return False
    
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT OR REPLACE INTO chat_ids (chat_id, first_name, last_name, username)
                    VALUES (?, ?, ?, ?)
                    """, (
                    user.id,
                    user.first_name,
                    user.last_name,
                    user.username
                ))
                conn.commit()
                toaster.show_toast("The Vocabulary Bot", f"New user: {user.first_name}", duration=5, threaded=True)
                logger.info(f"Attempted to save chat ID {chat_id}.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error saving chat ID {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error while saving user: {e}")
            return False

def delete_chat_id(chat_id) -> bool:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM chat_ids WHERE chat_id = ?", (chat_id,))
                conn.commit()
                if conn.total_changes > 0:
                    logger.info(f"Chat ID {chat_id} deleted.")
                    return True
                else:
                    logger.warning(f"Chat ID {chat_id} not found for deletion.")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Database error deleting chat ID {chat_id}: {e}")
            return False

def get_chat_ids_and_reminder_cycles() -> pd.DataFrame:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""SELECT chat_id, first_reminder, second_reminder, third_reminder, fourth_reminder, fifth_reminder FROM chat_ids""")
                df = pd.DataFrame(c.fetchall(), columns=['chat_id', 'first_reminder', 'second_reminder', 'third_reminder', 'fourth_reminder', 'fifth_reminder'])
                df['chat_id'] = df['chat_id'].astype(int)
                df['first_reminder'] = df['first_reminder'].astype(int)
                df['second_reminder'] = df['second_reminder'].astype(int)
                df['third_reminder'] = df['third_reminder'].astype(int)
                df['fourth_reminder'] = df['fourth_reminder'].astype(int)
                df['fifth_reminder'] = df['fifth_reminder'].astype(int)
                logger.info("Retrieved chat IDs from database.")
                return df
        except sqlite3.Error as e:
            logger.error(f"Database error getting chat IDs: {e}")
            return pd.DataFrame()

def change_reminder_cycle_of_a_user(chat_id, first=1, second=2, third=4, fourth=8, fifth=16) -> bool:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                # TODO: alter reminders
                c.execute("""""")
                
                logger.info(f"Altered {chat_id}'s reminder cycle.")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error altering a reminder ({chat_id}): {e}")
            return False
        except Exception as e:
            logger.error(f"Error while altering a reminder ({chat_id}): {e}")
            return False

def save_all_messages(chat_id, message):
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO messages (chat_id, message)
                    VALUES (?, ?)
                """, (chat_id, message))
                conn.commit()
                logger.info(f"Saved message from {chat_id}")
        except sqlite3.Error as e:
            logger.error(f"Error saving message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving message: {e}")






# --- Command Handlers ---
def escape_md(text):
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in escape_chars else c for c in text)

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_text = update.message.text

    save_all_messages(chat_id, message_text)
    logger.info(f"Received message from {chat_id}: {message_text}")

    try:
        wrd = message_text.lower().strip()
        check_db = get_word_from_db(wrd)
        if check_db == 'NOT IN DATABASE':
            the_id = add_word_to_db(wrd)
            if not the_id: 
                update.message.reply_text("I don't understand what you say!")
                return
            match_user_with_word(chat_id=chat_id, word_id=the_id[0])
            logger.info(f'The word ({wrd}) added to db for {chat_id}')
            word_id, definitions, examples = the_id
        else:
            word_id, definitions, examples = check_db
            match_user_with_word(chat_id=chat_id, word_id=word_id)
        
        defs = "\n".join(f"{i+1} {escape_md(defn)}" for i, defn in enumerate(definitions[:3]))
        exps = "\n".join(f"{i+1} {escape_md(ex)}" for i, ex in enumerate(examples[:3]))

        reply_text = (
            f"*Definitions of {escape_md(message_text)}:*\n"
            f"{defs}\n\n"
            f"*Examples:*\n{exps if examples else 'No examples available.'}"
        )

        update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN_V2)


    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        update.message.reply_text("Something went wrong while processing your request.")


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    logger.info(f"/start command received from {user_name} ({chat_id})")
    if save_chat_id(update.effective_chat):
        update.message.reply_text(
            f"Hello {user_name}! 👋\n"
            f"I am here to support your vocabulary level!\n"
            f"We will learn lots of new vocabulary together. "
            f"When you don't know a word, then just pass me the word!\n"
            f"\n/help for more detail."
            f"\n\n Kömen"
        )
    else:
        update.message.reply_text(
            f"Hi! I have faced with some problems while saving you in our database. Please contact with the admin:\n"
            f"\n- Kömen | 42enesbekdemir@gmail.com"
        )

def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    logger.info(f"/stop command received from {user_name} ({chat_id})")
    if delete_chat_id(chat_id):
        update.message.reply_text("You have successfully stopped the bot. You can restart the bot with /start command. Good Bye! 👋")
    else:
        update.message.reply_text(".") # TODO: add a text here

# TODO: add a help command

# TODO: add today's words command (the words that passed in last 24 hour)
# TODO: add this week's words command





# --- Main Function ---
def main() -> None:
    init_db()

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))    
    logger.info("Command handlers registered.")


    logger.info("Starting bot polling...")
    updater.start_polling()
    logger.info("Bot started successfully.")
    updater.idle()
    logger.info("Bot stopped.")

if __name__ == '__main__':
    main()