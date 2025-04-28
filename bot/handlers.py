import scraping.word_scraper as word
import ai.theAI as theAI
from database.databaseOps import init_db, get_word_from_db, add_word_to_db, match_user_with_word, get_chat_ids, save_chat_id, delete_chat_id, get_reminder_cycle_of_a_user, change_reminder_cycle_of_a_user, responsible_words, specific_time_word, save_all_messages

from config.settings import DB_PATH, LOG_FILE_PATH

### python-telegram-bot==13.15
from telegram import Update, ParseMode
from telegram.ext import Updater, CallbackContext

import requests
import logging
import sqlite3
import threading
import urllib3
from datetime import datetime, timedelta, timezone, time
from .utils import pronounce, essay_pronounce

db_lock = threading.Lock()
db_path = DB_PATH

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception as e:
    logger.warning(f"Could not disable InsecureRequestWarning: {e}")


# --- Command Handlers ---
def escape_md(text: str) -> str:
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in escape_chars else c for c in text)

def handle_message(update: Update, context: CallbackContext): # TODO: Check whether the user exist or not!!!!
    # FIXME: for poet: ERROR - Error in handle_message: Can't parse entities: character '.' is reserved and must be escaped with the preceding '\'
    # i guess the problem is that the word has no examples or definitions, so it returns None. When i try second time, it works.
    chat_id = update.effective_chat.id
    message_text = update.message.text

    save_all_messages(chat_id, message_text)

    try:
        wrd = message_text.lower().strip()
        check_db = get_word_from_db(wrd)
        if check_db == 'NOT IN DATABASE':
            the_id = add_word_to_db(wrd)
            if not the_id: 
                update.message.reply_text("I don't understand what you say!")
                return
            match_user_with_word(chat_id=chat_id, word_id=the_id[0])
            word_id, definitions, examples = the_id
        else:
            word_id, definitions, examples = check_db
            match_user_with_word(chat_id=chat_id, word_id=word_id)
        
        defs = "\n".join(f"{i+1} {escape_md(defn)}" for i, defn in enumerate(definitions[:3]))
        if len(examples) != 0 and examples[0] != '':
            exps = "\n".join(f"{i+1} {escape_md(ex)}" for i, ex in enumerate(examples[:3]))
            reply_text = (
                f"*Definitions of {escape_md(wrd)}:*\n"
                f"{defs}\n\n"
                f"*Examples:*\n{exps}"
            )
        else:
            reply_text = (
                f"*Definitions of {escape_md(wrd)}:*\n"
                f"{defs}"
                "\n\nThere are no examples available on Cambridge Dictionary for this word\."
            )
        update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        update.message.reply_text("Something went wrong while processing your request.")


def pronounce_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please provide a word to pronounce. (e.g. /pronounce word)")
        return

    word_to_pronounce = ''
    slow = False
    for arg in context.args:
        if arg.startswith('-'):
            if arg == '-slow' or arg == '-s':
                slow = True
            else:
                update.message.reply_text("Invalid option. Use -slow or -s for slow pronunciation.")
                return
        else:
            word_to_pronounce += arg + ' '
    
    word_to_pronounce = word_to_pronounce.strip().lower()
    
    audio_file = pronounce(word_to_pronounce, slow=slow, language='en')
    if audio_file:
        update.message.reply_voice(voice=audio_file, caption=f"Pronunciation of *{word_to_pronounce}*:", parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f"Could not generate pronunciation for '{word_to_pronounce}'.")
        logger.error(f"Could not generate pronunciation for '{word_to_pronounce}'.")



def define_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please provide a word to define. (e.g. /define word)")
        return

    chat_id = update.effective_chat.id
    
    for theWord in context.args:
        try:
            wrd = theWord.lower().strip()
            check_db = get_word_from_db(wrd)
            if check_db == 'NOT IN DATABASE':
                the_id = add_word_to_db(wrd)
                if not the_id: 
                    update.message.reply_text("I don't understand what you say!")
                    return
                word_id, definitions, examples = the_id
            else:
                word_id, definitions, examples = check_db
            
            defs = "\n".join(f"{i+1} {escape_md(defn)}" for i, defn in enumerate(definitions[:3]))
            if len(examples) != 0 and examples[0] != '':
                exps = "\n".join(f"{i+1} {escape_md(ex)}" for i, ex in enumerate(examples[:3]))
                reply_text = (
                    f"*Definitions of {escape_md(wrd)}:*\n"
                    f"{defs}\n\n"
                    f"*Examples:*\n{exps if examples else 'No examples available.'}"
                )
            else:
                reply_text = (
                    f"*Definitions of {escape_md(wrd)}:*\n"
                    f"{defs}"
                    "\n\nThere are no examples available on Cambridge Dictionary for this word\."
                )

            text = []
            char_limit = 4000
            if len(reply_text) > char_limit:
                cb = 0
                ca = 0
                for i in range(0, len(reply_text), char_limit):
                    if i+cb+char_limit > len(reply_text):
                        text.append(reply_text[i+cb:])
                        break
                    while reply_text[i+ca+char_limit] != ' ':
                        ca += 1
                    text.append(reply_text[i+cb:i+ca+char_limit])
                    cb = ca
                    ca = 0
            else:
                text = [reply_text]

            for rply in text:
                update.message.reply_text(rply, parse_mode=ParseMode.MARKDOWN_V2)


        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            update.message.reply_text(f"Something went wrong while processing your request. ({theWord})")




def get_words_command(update: Update, context: CallbackContext) -> list[str]:
    command = update.message.text.split()[0][1:] 
    
    periods = {
        "words": "all",
        "today": "today",
        "this_week": "this_week",
        "responsibility": "responsibility"
    }
    if command in periods:
        period = periods.get(command)
    else:
        update.message.reply_text("Invalid command. Please use /words, /today, or /this_week.")
        return

    chat_id = update.effective_chat.id

    time_condition = ""
    now = datetime.now(timezone.utc)

    if period == "today":
        if now.hour < 12:
            start_of_day = now - timedelta(hours=18)
        else:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        time_condition = "AND uw.created_at >= ?"
        time_params = [start_of_day]
    elif period == "this_week":
        start_time = now - timedelta(days=7)
        time_condition = "AND uw.created_at >= ?"
        time_params = [start_time]
    elif period == "responsibility":
        reminders = get_reminder_cycle_of_a_user(chat_id)
        if reminders is None:
            update.message.reply_text("You don't have any reminders set.")
            return
        valid_dates = [(now - timedelta(days=reminder)).date() for reminder in reminders]
        placeholders = ', '.join(['?'] * len(valid_dates))
        time_condition = f"AND DATE(uw.created_at) IN ({placeholders})"
        time_params = valid_dates
    else:
        time_params = []

    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = f'''
                SELECT w.word FROM words w
                JOIN user_words uw ON w.id = uw.word_id
                WHERE uw.chat_id = ? {time_condition}
            '''
            cursor.execute(query, [chat_id] + time_params)
            result = cursor.fetchall()
            conn.close()

        if result:
            words = [row[0] for row in result]
        else:
            logger.warning(f"No words found for chat ID {chat_id} (period: {period}).")
            words = []
    except sqlite3.Error as e: 
        logger.error(f"SQLite error: {e}")
        words = []
    except Exception as e:
        logger.error(f"Error retrieving user words by command ({chat_id}, {period}): {e}")
        words = []

    if words:
        words_text = "\n".join(f"{i+1}. {word}" for i, word in enumerate(words))
        dct = {
            "all": "all time",
            "today": "today",
            "this_week": "this week",
            "responsibility": "your responsibility dates"
        }
        update.message.reply_text(
            f"Here are your words ({len(words)}) for {dct[period]}:\n\n{words_text}"
        )
    else:
        update.message.reply_text(
            f"You don't have any words in your vocabulary yet. "
            f"Please send me a word to start learning!"
        )
    logger.info(f"Words command executed for chat ID {chat_id} (period: {period}).")


def get_reminder_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    reminders = get_reminder_cycle_of_a_user(chat_id)
    if reminders is None:
        update.message.reply_text("You don't have any reminders set.")
        return

    reminder_text = (
        f"Your reminder cycle:\n"
        f"""1st reminder: {'Today' if reminders[0] == 0 else f"{reminders[0]} day{'s' if reminders[0]>1 else ''}"}\n"""
        f"2nd reminder: {reminders[1]} day{'s' if reminders[1] > 1 else ''} ago\n"
        f"3rd reminder: {reminders[2]} days ago\n"
        f"4th reminder: {reminders[3]} days ago\n"
        f"5th reminder: {reminders[4]} days ago\n"
        f"\nYou can change your reminder cycle with /set_reminders command."
    )
    update.message.reply_text(reminder_text)
    logger.info(f"Reminder command executed for chat ID {chat_id}.")

def set_reminder_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if len(context.args) != 5:
        update.message.reply_text("Please provide 5 reminder intervals in days like the example:\n/set_reminders 1 2 4 8 16")
        return

    try:
        reminders = [int(arg) for arg in context.args]
        if any(reminder < 0 for reminder in reminders):
            raise ValueError("Reminder intervals must be non-negative.")

        if change_reminder_cycle_of_a_user(chat_id, *reminders):
            update.message.reply_text(f"Your reminder cycle has been updated successfully.")
            logger.info(f"Reminder cycle updated for chat ID {chat_id}.")
        else:
            update.message.reply_text("Failed to update your reminder cycle.")
            logger.error(f"Failed to update reminder cycle for chat ID {chat_id}.")
    except ValueError as e:
        update.message.reply_text(f"Invalid input: {e}")
        logger.error(f"Invalid input for reminder command ({chat_id}): {e}")
    except Exception as e:
        update.message.reply_text("An error occurred while updating your reminder cycle.")
        logger.error(f"Error while updating reminder cycle ({chat_id}): {e}")


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
        update.message.reply_text("You are not in our database. Please contact with the admin:\n\n- Kömen | 42enesbekdemir@gmail.com")

def stats_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    logger.info(f"/stats command received from {user_name} ({chat_id})")
    try:
        with db_lock:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT created_at FROM user_words WHERE chat_id = ?''', (chat_id,))
            all_words = cursor.fetchall()
            conn.close()

        all_dates = [datetime.strptime(t[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) for t in all_words]
        responsibility_sum = len(responsible_words(chat_id))
        now = datetime.now(timezone.utc)
        if now.hour < 12:
            start_of_day = now - timedelta(hours=18)
        else:
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_week = now - timedelta(days=7)
        
        today_sum = 0
        this_week_sum = 0
        for date in all_dates:
            if date >= start_of_day:
                today_sum += 1
            if date >= start_week:
                this_week_sum += 1

        all_days = [date.date() for date in all_dates]
        streak = 0
        while streak < len(all_dates) and (now.date() - timedelta(days=streak)) in all_days:
            streak += 1

        text = (
            f"Hello {user_name}! 👋\n"
            f"Here are your stats:\n\n"
            f"You have added a total of <b>{len(all_dates)}</b>{'❤️‍🔥' if len(all_dates) >= 5 else ''} words to your vocabulary.\n"
            f"{today_sum if today_sum < len(all_dates) else 'All'} of them are added today. /today\n"
            f"{this_week_sum if this_week_sum < len(all_dates) else 'All'} of them are added this week. /this_week\n"
            f"{responsibility_sum if responsibility_sum < len(all_dates) else 'All'} of them are your responsibility for today. /responsibility"
            f"\n\nYour current streak is <b>{streak}</b>{'💀' if streak >= 10 else '🔥' if streak >=5 else '😎' if streak >= 3 else ''} day{'s' if streak >= 2 else ''}.\n"
            f"\n\nYou can view your words with /words command.\n")            

        update.message.reply_text(text, parse_mode=ParseMode.HTML)
        logger.info(f"Stats command executed for chat ID {chat_id}.")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        update.message.reply_text("An error occurred while retrieving stats.")
    except Exception as e:
        logger.error(f"Error in stats command ({chat_id}): {e}")
        update.message.reply_text("An error occurred while retrieving stats.")

def delete_word(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if len(context.args) == 0:
        update.message.reply_text("Please provide a word to delete. (e.g. /delete word)")
        return

    word_to_delete = context.args[0].lower()
    with db_lock:
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('''DELETE FROM user_words WHERE chat_id = ? AND word_id IN (SELECT id FROM words WHERE word = ?)''', (chat_id, word_to_delete))
                conn.commit()
                if conn.total_changes > 0:
                    update.message.reply_text(f"The word '{word_to_delete}' has been deleted from your vocabulary.")
                    logger.info(f"Deleted word '{word_to_delete}' for chat ID {chat_id}.")
                else:
                    update.message.reply_text(f"The word '{word_to_delete}' was not found in your vocabulary.")
                    logger.warning(f"Word '{word_to_delete}' not found for chat ID {chat_id}.")
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            update.message.reply_text("An error occurred while deleting the word.")
        except Exception as e:
            logger.error(f"Error deleting word ({chat_id}, {word_to_delete}): {e}")
            update.message.reply_text("An error occurred while deleting the word.")


def turkish_meaning_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please provide a word to translate. (e.g. /tr word)")
        return

    word_to_translate = context.args[0].lower()
    
    # TODO: Check if the word is already in the database
        
    turkish_meaning = word.scrape_turkish_meaning(word_to_translate) 
    if turkish_meaning:
        turkish_meaning_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(turkish_meaning[:3]))
        update.message.reply_text(f"*Turkish meaning of {word_to_translate}:*\n{turkish_meaning_text}", parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(f"No Turkish meaning found for '{word_to_translate}'.")

def help_command(update: Update, context: CallbackContext):
    text = (
        "🌟 *Welcome to Vocabulary Bot!* 🌟\n\n"
        "*How I can help you:*\n"
        "When you encounter a word you don't know, just send it to me! I'll provide you with its definitions and examples.\n\n"
        "🛠 *Commands you can use:*\n"
        "/start - Start the bot\n"
        "/stop - Stop the bot\n"
        "/stats - View your vocabulary stats\n"
        "/help - Show this help message\n"
        "`/any_command -help` - Show help for any command\n"
        "/define `[word]` - Get all definitions of a word\n"
        "/tr `[word]` - Get the Turkish meaning of a word\n"
        "/pronounce `[word]` - Get the pronunciation of a word\n"
        "/delete `[word]` - Delete a word from your vocabulary\n"
        "/words - View all your words\n"
        "/today - View words added today\n"
        "/this\_week - View words added this week\n"
        "/responsibility - View words you're responsible for today\n"
        "/essay - Generate an essay using your responsible words\n"
        "/reminder - View your reminder cycle\n"
        "/set\_reminders - Update your reminder cycle\n\n"
        "💡 *Quick Tip:*\n"
        "You can also send me a word directly to get its definitions and examples.\n"
        "Happy learning! 🎉📚\n"
        "\n- *Kömen*✨"
    )
    # escaped_text = escape_md(text)
    update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN
    )


def send_essay_to_user(update: Update, context: CallbackContext) -> None:
    try:
        now = datetime.now(timezone.utc)
        chat_id = update.effective_chat.id
        words = responsible_words(chat_id)
        if not words:
            update.message.reply_text("You don't have any words to generate an essay.")
            return


        if len(context.args) == 0:
            placeholder_message = update.message.reply_text("Generating essay...")
            essay = theAI.generate_an_essay_with_words(words)
            voice = essay_pronounce(essay, slow=False, language='en')
        else:
            theme = ''
            length = ''
            typ = ''
            level = 'B2'
            slow = False
            words_range = 'all'
            for arg in context.args:
                if arg.startswith('-'):
                    if arg == '-help':
                        update.message.reply_text("Usage: /essay [-story | -essay | -paragraph] [-very-short | -short | -medium | -long | -very-long] [-A1 | -A2 | -B1 | -B2 | -C1 | -C2] [-today | -this-week | -all | -responsibility] [theme] \n\nFor example: /essay -story -short a day in the life of a student")
                        return
                    elif arg.startswith('-') and arg in ['-story', '-essay', '-paragraph']:
                        typ = arg[1:]
                    elif arg.startswith('-') and arg in ['-very-short', '-short', '-medium', '-long', '-very-long']:
                        length = arg[1:]
                    elif arg.startswith('-') and arg.upper() in ['-A1', '-A2', '-B1', '-B2', '-C1', '-C2']:
                        level = arg[1:].upper()
                    elif arg.startswith('-') and arg in ['-slow', '-s']:
                        slow = True
                    elif arg.startswith('-') and arg in ['-today', '-this-week', '-all', '-responsibility']:
                        words_range = arg[1:]
                        if words_range == 'today':
                            words = specific_time_word(chat_id, date='today')
                        elif words_range == 'this_week':
                            words = specific_time_word(chat_id, date='this_week')
                        elif words_range == 'all':
                            with db_lock:
                                conn = sqlite3.connect(db_path)
                                cursor = conn.cursor()
                                query = f'''
                                    SELECT w.word FROM words w
                                    JOIN user_words uw ON w.id = uw.word_id
                                    WHERE uw.chat_id = ?
                                '''
                                cursor.execute(query, [chat_id])
                                result = cursor.fetchall()
                                conn.close()
                                if result:
                                    words = [row[0] for row in result]
                                else:
                                    update.message.reply_text("No words found in your vocabulary.")
                                    return
                    else:
                        update.message.reply_text(f"Unknown argument: {arg}. Use /essay -help for usage.")
                        return
                else:
                    theme += arg + ' '
            placeholder_message = update.message.reply_text("Generating essay...")
            essay = theAI.generate_an_essay_with_words(words, theme=theme.strip(), length=length, typ=typ, level=level)
            voice = essay_pronounce(essay, slow=slow, language='en')
        if not essay:
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=placeholder_message.message_id,
                text="Failed to generate an essay. Please try again later.",
            )
            return

        essays = []
        char_limit = 4000
        if len(essay) > char_limit:
            cb = 0
            ca = 0
            for i in range(0, len(essay), char_limit):
                if i+cb+char_limit > len(essay):
                    essays.append(essay[i+cb:])
                    break
                while essay[i+ca+char_limit] != ' ':
                    ca += 1
                essays.append(essay[i+cb:i+ca+char_limit])
                cb = ca
                ca = 0

        else:
            essays = [essay]
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=placeholder_message.message_id,
            text=essays[0],
            parse_mode=ParseMode.MARKDOWN 
        )
        for chunk in essays[1:]:
            update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        
        context.bot.send_voice(chat_id=chat_id, voice=voice, caption="Here is your essay!")
        
        logger.info(f"Sent essay to chat ID {chat_id}. It took {datetime.now(timezone.utc) - now} seconds.")
    except Exception as e:
        logger.error(f"Error in send_essay_to_user: {e}")
        update.message.reply_text("An error occurred while generating the essay.")
        



def send_daily_essays(context: CallbackContext) -> None:
    logger.info("Sending daily essays...")
    chat_ids = get_chat_ids()
    if len(chat_ids) == 0:
        logger.info("No chat IDs found in the database.")
        return

    for chat_id in chat_ids:
        logger.info(f"Sending daily essay to chat ID {chat_id}...")
        try:
            words = responsible_words(chat_id)
            if not words:
                continue

            essay = theAI.generate_an_essay_with_words(words) # TODO: make it async
            voice = essay_pronounce(essay, slow=False, language='en')
            parts = essay.split('**')
            for i in range(1, len(parts), 2):
                parts[i] = f'<b>{parts[i]}</b>'
            essay = ''.join(parts)
            if not essay:
                logger.warning(f"Failed to generate essay for chat ID {chat_id}.")
                continue
        
            essay = '<b>Your daily essay:</b>\n\n' + essay
            essays = []
            char_limit = 4000
            if len(essay) > char_limit:
                cb = 0
                ca = 0
                for i in range(0, len(essay), char_limit):
                    if i+cb+char_limit > len(essay):
                        essays.append(essay[i+cb:])
                        break
                    while essay[i+ca+char_limit] != ' ':
                        ca += 1
                    essays.append(essay[i+cb:i+ca+char_limit])
                    cb = ca
                    ca = 0
            else:
                essays = [essay]

            for chunk in essays:
                context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode=ParseMode.HTML) # FIXME: Convert this to markdown v2
            
            context.bot.send_voice(chat_id=chat_id, voice=voice, caption="Here is your daily essay!")

        except Exception as e:
            logger.error(f"Error sending daily essay to chat ID {chat_id}: {e}")
            continue
        logger.info(f"Daily essay sent to chat ID {chat_id}.")


def test(update: Update, context: CallbackContext): # TODO: remove this function
    send_daily_essays(context)
    update.message.reply_text("Test function executed.")
