from bot.handlers import handle_message
from database.databaseOps import init_db
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import logging
from config.settings import TELEGRAM_BOT_TOKEN, DAILY_ESSAYS_TIME, LOG_FILE_PATH

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


from bot.handlers import (
    start, stop, delete_word, help_command, get_words_command,
    stats_command, get_reminder_command, set_reminder_command,
    send_essay_to_user, turkish_meaning_command, define_command,
    pronounce_command, send_daily_essays, 
    test
)



def main() -> None:
    init_db()

    token = TELEGRAM_BOT_TOKEN
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    dispatcher.add_handler(CommandHandler("test", test)) # TODO: remove this line

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("delete", delete_word))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    dispatcher.add_handler(CommandHandler("words", get_words_command))
    dispatcher.add_handler(CommandHandler("today", get_words_command))
    dispatcher.add_handler(CommandHandler("this_week", get_words_command))
    dispatcher.add_handler(CommandHandler("responsibility", get_words_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    
    dispatcher.add_handler(CommandHandler("reminder", get_reminder_command))
    dispatcher.add_handler(CommandHandler("set_reminders", set_reminder_command))

    dispatcher.add_handler(CommandHandler("essay", send_essay_to_user))
    
    dispatcher.add_handler(CommandHandler("tr", turkish_meaning_command))
    dispatcher.add_handler(CommandHandler("define", define_command))
    
    dispatcher.add_handler(CommandHandler("pronounce", pronounce_command))
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))    

    job_queue.run_daily(
        send_daily_essays,
        time=DAILY_ESSAYS_TIME,
        name="send_daily_essays"
    )
    
    logger.info("Starting bot polling...")
    updater.start_polling()
    logger.info("Bot started successfully.")

    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast("The Vocabulary Bot", "The Vocabulary Bot has just started!", duration=5, threaded=True)

    updater.idle()
    logger.info(f"Bot stopped.\n{'='*125}")

if __name__ == '__main__':
    main()

    # TODO: Add exam functionality (multiple choice, fill in the blanks, etc.)
    # TODO: Add email functionality (send daily essays to email) and email subscription (/subscribe_email [email])
    
    # TODO: Research what is inline mode and how to use it
    
    # TODO: Asnc functions for scraping and ai operations
    
    # TODO: SM-2 (super memory algorithm) ?
    
    # TODO: /generate_example command to generate an example sentence using a word
    # TODO: Add commands /synonyms [word] and /antonyms [word] (we can do it with theAI)
    
    # TODO: /simplify [word] to ask theAI to explain the definition in simpler terms
    
    # TODO: Offer pre-defined lists of words users can add (e.g., "Business English", "Academic Vocabulary", "Common Phrasal Verbs")
    
    # TODO: /essay -today (-this_week) to generate an essay using the words added today 