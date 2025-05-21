from openai import OpenAI
import logging
import datetime
from config.settings import AI_API, LOG_FILE_PATH, AI_MODEL
from random import shuffle

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO
)
ai_logger = logging.getLogger(__name__)


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_API
)

def generate_an_essay_with_words(vocab_words, theme=None, length=None, typ="story", level="B2"):
    now = datetime.datetime.now()
    shuffle(vocab_words)
    words_str = ", ".join(vocab_words)
    if typ not in ["story", "essay", "paragraph"]:
        typ = "story"
    word_count = 1000 if length == "very-long" else 750 if length == "long" else 500 if length == "medium" else 300 if length == "short" else 150 if length == "very-short" else None
    
    if word_count is None:
        word_count = 75 if len(vocab_words) < 5 else len(vocab_words) * 15 if len(vocab_words) < 10 else len(vocab_words) * 12 if len(vocab_words) < 20 else len(vocab_words) * 10 if len(vocab_words) < 30 else len(vocab_words) * 8
    
    theme_instruction = f" about {theme}" if theme != '' and theme != None else ""
    
    prompt = f"""
    Write a {word_count}-word {typ}{theme_instruction} that naturally incorporates the following vocabulary words: 
    {words_str}

    The {typ} should have a clear beginning, middle, and end. It must be engaging, imaginative, and easy to follow. 
    Use vivid, descriptive language to create imagery and evoke emotion, but avoid complex sentence structures or obscure references. 
    Each vocabulary word must be used **bolded**, in proper context, and blended seamlessly into the narrative. 
    Do not define the words directly or list them.

    Ensure correct grammar and punctuation throughout.
    Return only the {typ}, with no additional text or explanations.
    """
    system_instruction = f"""
    You are a master storyteller and educator. Your mission is to teach vocabulary by crafting emotionally engaging, context-rich {typ}s. 
    You must never define the vocabulary words directly; instead, demonstrate their meanings through natural use in the narrative. 

    All writing should be appropriate for a reader at the {level} English level—clear, expressive, and grammatically sound.
    Style should be suitable for markdown format.
    """

    err = 0
    ai_logger.info(f"Generating an essay - Theme: {theme_instruction}, Essay Word Count: {word_count}, Vocab Count: {len(vocab_words)}, Type: {typ}, Level: {level}, Model: {AI_MODEL}")
    for _ in range(3):
        try:
            completion = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            )
            essay = completion.choices[0].message.content
            if essay == "":
                raise ValueError("Empty response from AI")
            ai_logger.info(f"Essay generated in {datetime.datetime.now() - now} seconds. Essay length: {len(essay.split())} words.")
            return essay
        except Exception as e:
            if err == 2: 
                ai_logger.error(f"Essay couldn't generated in {datetime.datetime.now() - now} seconds")
                return f"An error occurred: {e}"
            err += 1
            ai_logger.warning(f"Error generating essay: {e}, retrying...")