from config.settings import LOG_FILE_PATH, RETRY_LIMIT, RETRY_DELAY

from gtts import gTTS
from io import BytesIO

from telegram import Update, ParseMode
from telegram.error import NetworkError, Unauthorized, BadRequest, TimedOut, RetryAfter, TelegramError

import logging
import time

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



def pronounce(text, slow=False, language='en'):
    tts = gTTS(text=text, lang=language, slow=slow)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file


def essay_pronounce(text, slow=False, language='en'): # TODO: it is too robotic, find another way to pronounce essays, also it takes too long to generate the audio file.
    text = text.replace('\n', '.').replace('*', '').replace('_', '').replace('-', '')
    tts = gTTS(text=text, lang=language, slow=slow)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file

def escape_md(text: str) -> str:
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in escape_chars else c for c in text)

def send_message_UPDATE(update: Update, text: str, parse_mode = None, sender='-') -> str:
    for attempt in range(RETRY_LIMIT):
        try:
            msg = update.message.reply_text(text, parse_mode=parse_mode)
            return msg
        except NetworkError as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except Unauthorized as e:
            logger.error(f"Unauthorized error: {e}. User may have blocked the bot ({sender})")
            return 'UNAUTHORIZED'
        except BadRequest as e:
            logger.error(f"BadRequest error: {e}. Invalid message format ({sender})")
            return 'BAD_REQUEST'
        except TimedOut as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"TimedOut error: {e}. Retrying... ({sender})")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except RetryAfter as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"RetryAfter error: {e}. Retrying after {e.retry_after} seconds ({sender})")
            time.sleep(e.retry_after)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}. ({sender})")
            return 'ERROR'
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"Unexpected error: {e}. ({sender})")

def send_message_CONTEXT(context, text: str, chat_id:int, parse_mode = None, sender='-') -> str:
    for attempt in range(RETRY_LIMIT):
        try:
            msg = context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            return msg
        except NetworkError as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except Unauthorized as e:
            logger.error(f"Unauthorized error: {e}. User may have blocked the bot ({sender})")
            return 'UNAUTHORIZED'
        except BadRequest as e:
            logger.error(f"BadRequest error: {e}. Invalid message format ({sender})")
            return 'BAD_REQUEST'
        except TimedOut as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"TimedOut error: {e}. Retrying... ({sender})")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except RetryAfter as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"RetryAfter error: {e}. Retrying after {e.retry_after} seconds ({sender})")
            time.sleep(e.retry_after)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}. ({sender})")
            return 'ERROR'
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send message after {RETRY_LIMIT} attempts ({sender}): {e}")
                return 'ERROR'
            logger.error(f"Unexpected error: {e}. ({sender})")


def edit_message(context, chat_id, message_id, text, parse_mode=None):
    for attempt in range(RETRY_LIMIT):
        try:
            msg = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=parse_mode)
            return msg
        except NetworkError as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to edit message after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except Unauthorized as e:
            logger.error(f"Unauthorized error: {e}. User may have blocked the bot")
            return 'UNAUTHORIZED'
        except BadRequest as e:
            logger.error(f"BadRequest error: {e}. Invalid message format")
            return 'BAD_REQUEST'
        except TimedOut as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to edit message after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"TimedOut error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except RetryAfter as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to edit message after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"RetryAfter error: {e}. Retrying after {e.retry_after} seconds")
            time.sleep(e.retry_after)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}.")
            return 'ERROR'
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to edit message after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Unexpected error: {e}.")


def send_audio_CONTEXT(context, chat_id, audio, title):
    for attempt in range(RETRY_LIMIT):
        try:
            msg = context.bot.send_audio(chat_id=chat_id, audio=audio, title=title)
            return msg
        except NetworkError as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except Unauthorized as e:
            logger.error(f"Unauthorized error: {e}. User may have blocked the bot")
            return 'UNAUTHORIZED'
        except BadRequest as e:
            logger.error(f"BadRequest error: {e}. Invalid message format")
            return 'BAD_REQUEST'
        except TimedOut as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"TimedOut error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except RetryAfter as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"RetryAfter error: {e}. Retrying after {e.retry_after} seconds")
            time.sleep(e.retry_after)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}.")
            return 'ERROR'
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Unexpected error: {e}.")


def reply_audio_UPDATE(update, audio, title, parse_mode=None):
    for attempt in range(RETRY_LIMIT):
        try:
            msg = update.message.reply_audio(audio=audio, title=title, parse_mode=parse_mode)
            return msg
        except NetworkError as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Network error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except Unauthorized as e:
            logger.error(f"Unauthorized error: {e}. User may have blocked the bot")
            return 'UNAUTHORIZED'
        except BadRequest as e:
            logger.error(f"BadRequest error: {e}. Invalid message format")
            return 'BAD_REQUEST'
        except TimedOut as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"TimedOut error: {e}. Retrying...")
            time.sleep(RETRY_DELAY**(attempt + 1))
        except RetryAfter as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"RetryAfter error: {e}. Retrying after {e.retry_after} seconds")
            time.sleep(e.retry_after)
        except TelegramError as e:
            logger.error(f"Telegram error: {e}.")
            return 'ERROR'
        except Exception as e:
            if attempt == RETRY_LIMIT - 1:
                logger.error(f"Failed to send audio after {RETRY_LIMIT} attempts: {e}")
                return 'ERROR'
            logger.error(f"Unexpected error: {e}.")