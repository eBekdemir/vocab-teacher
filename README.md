# AI Powered Vocabulary Teacher Bot
<a href="https://t.me/TheVocabBot" target="_blank">Visit the Vocabulary Teacher Bot on Telegram</a>

The Vocabulary Teacher Bot is a Telegram bot designed to help users improve their vocabulary through interactive learning. It provides definitions, examples, pronunciation, and even generates essays using the words you learn with AI. The bot also includes features like reminders, statistics, and customizable learning cycles.
<br>
The main purpose of this bot is to assist users in expanding their vocabulary in an engaging and structured way. By providing definitions, examples, and pronunciation, the bot ensures a comprehensive learning experience. Additionally, features like **essay generation** and reminders help users _retain_ and _apply_ their knowledge effectively. Whether you're preparing for exams, improving your language skills, or just exploring new words, this bot is designed to make vocabulary learning enjoyable and efficient.

## Features

- **Word Definitions and Examples**: Get definitions and examples for any word.
- **Pronunciation**: Listen to the pronunciation of words.
- **Turkish Translation**: Translate words into Turkish.
- **Essay Generation**: Generate essays using your vocabulary words.
- **Reminders**: Set reminders to review words at specific intervals.
- **Statistics**: Track your learning progress and streaks.
- **Customizable Learning**: Add, delete, and manage your vocabulary words.
- **Daily Essays**: Receive daily essays based on your responsible words.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/eBekdemir/vocab-teacher.git
   cd vocab-teacher
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the `config` directory.
   - Add the following variables:
     ```
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     DB_PATH=theDataBase.db
     LOG_FILE_PATH=logs/bot.log
     OPENROUTER_DEEPSEEK_R1_API_KEY=your_openrouter_api_key
     ```

## Usage

1. Start the bot:
   ```bash
   python main.py
   ```

2. Interact with the bot on Telegram:
   - Use `/start` to begin.
   - Send any word to get its definition and examples.
   - Use `/help` to see all available commands.

## Commands

- `/start`: Start the bot.
- `/stop`: Stop the bot.
- `/define [word]`: Get definitions and examples for a word.
- `/tr [word]`: Get the Turkish meaning of a word.
- `/pronounce [word]`: Listen to the pronunciation of a word.
- `/delete [word]`: Delete a word from your vocabulary.
- `/words`: View all your words.
- `/today`: View words added today.
- `/this_week`: View words added this week.
- `/responsibility`: View words you're responsible for today.
- `/essay`: Generate an essay using your vocabulary words.
- `/reminder`: View your reminder cycle.
- `/set_reminders [intervals]`: Update your reminder cycle.
- `/stats`: View your learning statistics.
- `/help`: Show help information.

<br><br>
Happy learning! 🎉
