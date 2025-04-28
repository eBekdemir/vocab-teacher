import sqlite3
import threading
import logging
from datetime import datetime, timedelta, timezone
import scraping.word_scraper as word
from config.settings import DB_PATH, LOG_FILE_PATH

db_path = DB_PATH
db_lock = threading.Lock()


logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


from win10toast import ToastNotifier
toaster = ToastNotifier() # i use this only for new user notifications


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
                        email TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        first_reminder INTEGER DEFAULT 0,
                        second_reminder INTEGER DEFAULT 1,
                        third_reminder INTEGER DEFAULT 3,
                        fourth_reminder INTEGER DEFAULT 6,
                        fifth_reminder INTEGER DEFAULT 14,
                        english_level TEXT DEFAULT B2,
                        UNIQUE (chat_id) ON CONFLICT REPLACE
                        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY,
                        word TEXT,
                        definitions TEXT,
                        examples TEXT,
                        turkish_meaning TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (word) ON CONFLICT REPLACE
                        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_words (
                        id INTEGER PRIMARY KEY,
                        chat_id INTEGER,
                        word_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chat_ids (chat_id),
                        FOREIGN KEY (word_id) REFERENCES words (id),
                        UNIQUE (chat_id, word_id) ON CONFLICT REPLACE
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

def add_word_to_db(wrd: str) -> tuple[int, list[str], list[str]]:
    definitions, examples = word.scrape_the_word(wrd)
    turkish = word.scrape_turkish_meaning(wrd)
    if not definitions and not examples:
        logger.warning(f"No definitions or examples found for word: {word}")
        return None
    if not turkish:
        logger.warning(f"No turkish meaning found for word: {word}")
        turkish = None
    
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO words (word, definitions, examples, turkish_meaning) VALUES (?, ?, ?, ?)''',
                    (wrd, ';;;'.join(definitions), ';;;'.join(examples), ';;;'.join(turkish) if turkish else None))
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
            logger.info(f"Retrieved definitions and examples for word '{wrd}' from database.")
            return word_id, definitions.split(';;;'), examples.split(';;;')
        else:
            logger.warning(f"Word '{wrd}' not found in database.")
            return 'NOT IN DATABASE'
    except sqlite3.Error as e: 
        logger.error(f"SQLite error: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Error retrieving a word ({wrd}): {e}")
        return None, None, None


def match_user_with_word(chat_id: int, word_id: int) -> bool: 
    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO user_words (chat_id, word_id) VALUES (?, ?)''', (chat_id, word_id)) 
            conn.commit()
            conn.close()
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
                    INSERT INTO chat_ids (chat_id, first_name, last_name, username)
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

def get_chat_ids() -> list[int]:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""SELECT chat_id FROM chat_ids""")
                chat_ids = c.fetchall()
                chat_ids = [chat_id[0] for chat_id in chat_ids]
                return chat_ids
        except sqlite3.Error as e:
            logger.error(f"Database error getting chat IDs: {e}")
            return []

def get_reminder_cycle_of_a_user(chat_id: int) -> tuple[int, int, int, int, int]:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""SELECT first_reminder, second_reminder, third_reminder, fourth_reminder, fifth_reminder FROM chat_ids WHERE chat_id = ?""", (chat_id,))
                result = c.fetchall()
                result = result[0] if result else None
                if result:
                    logger.info(f"Retrieved reminder cycle for chat ID {chat_id}.")
                    return result
                else:
                    logger.warning(f"No reminder cycle found for chat ID {chat_id}.")
                    return None
        except sqlite3.Error as e:
            logger.error(f"Database error getting reminder cycle ({chat_id}): {e}")
            return None
        except Exception as e:
            logger.error(f"Error while getting reminder cycle ({chat_id}): {e}")
            return None

def change_reminder_cycle_of_a_user(chat_id, first=1, second=2, third=4, fourth=8, fifth=16) -> bool:
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE chat_ids
                    SET first_reminder = ?,
                        second_reminder = ?,
                        third_reminder = ?,
                        fourth_reminder = ?,
                        fifth_reminder = ?
                    WHERE chat_id = ?
                """, (first, second, third, fourth, fifth, chat_id))
                conn.commit()
                if conn.total_changes == 0:
                    logger.warning(f"No changes made to reminder cycle for chat ID {chat_id}.")
                    return False                    
                
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
        except sqlite3.Error as e:
            logger.error(f"Error saving message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving message: {e}")


def responsible_words(chat_id: int) -> list[str]:
    now = datetime.now(timezone.utc)
    reminders = get_reminder_cycle_of_a_user(chat_id)
    if reminders is None:
        return
    time_params = [(now - timedelta(days=reminder)).date() for reminder in reminders]
    placeholders = ', '.join(['?'] * len(time_params))
    time_condition = f"AND DATE(uw.created_at) IN ({placeholders})"

    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute(f"""
                    SELECT w.word FROM words w
                    JOIN user_words uw ON w.id = uw.word_id
                    WHERE uw.chat_id = ? {time_condition}
                """, (chat_id, *time_params))
                result = c.fetchall()
                if result:
                    words = [row[0] for row in result]
                    logger.info(f"Retrieved responsible words for chat ID {chat_id}.")
                    return words
                else:
                    logger.warning(f"No responsible words found for chat ID {chat_id}.")
                    return []
        except sqlite3.Error as e:
            logger.error(f"Database error getting responsible words ({chat_id}): {e}")
            return []
        except Exception as e:
            logger.error(f"Error while getting responsible words ({chat_id}): {e}")
            return []

def specific_time_word(chat_id: int, date: list[int] = 'today') -> list[str]:
    now = datetime.now(timezone.utc)
    if date == 'today':
        if now.hour < 12:
            start_of_day = now - timedelta(hours=18)
        else:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        time_condition = "AND uw.created_at >= ?"
        time_params = [start_of_day]
    elif date == 'this_week':
        start_time = now - timedelta(days=7)
        time_condition = "AND uw.created_at >= ?"
        time_params = [start_time]
    else:
        time_params = [(now - timedelta(days=dt)).date() for dt in date] # date day ago
    placeholders = ', '.join(['?'] * len(time_params))
    time_condition = f"AND DATE(uw.created_at) IN ({placeholders})"

    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute(f"""
                    SELECT w.word FROM words w
                    JOIN user_words uw ON w.id = uw.word_id
                    WHERE uw.chat_id = ? {time_condition}
                """, (chat_id, *time_params))
                result = c.fetchall()
                if result:
                    words = [row[0] for row in result]
                    logger.info(f"Retrieved specific_time_word words for chat ID {chat_id}.")
                    return words
                else:
                    logger.warning(f"No specific_time_word words found for chat ID {chat_id}.")
                    return []
        except sqlite3.Error as e:
            logger.error(f"Database error getting specific_time_word words ({chat_id}): {e}")
            return []
        except Exception as e:
            logger.error(f"Error while getting specific_time_word words ({chat_id}): {e}")
            return []

