from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
open_router_api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=open_router_api_key
)

def generate_an_essay_with_words(vocab_words, theme=None, length=None, typ="story"):
    words_str = ", ".join(vocab_words)
    
    word_count = 1000 if length == "very-long" else 750 if length == "long" else 500 if length == "medium" else 300 if length == "short" else 150 if length == "very-short" else None
    
    if word_count is None:
        word_count = 75 if len(vocab_words) < 5 else len(vocab_words) * 15 if len(vocab_words) < 10 else len(vocab_words) * 12 if len(vocab_words) < 20 else len(vocab_words) * 10 if len(vocab_words) < 30 else len(vocab_words) * 8
    
    theme_instruction = f" about {theme}" if theme != '' and theme != None else ""
    
    prompt = f"""
    Write a {word_count}-word {typ}{theme_instruction} that naturally incorporates the following vocabulary words: 
    {words_str}.

    The {typ} should be engaging and imaginative, with a clear beginning, middle, and end. 
    Use descriptive language to create vivid imagery and evoke emotions in the reader. 
    The vocabulary words should be used in a way that enhances the {typ}, rather than feeling forced or out of place. 
    Aim for a balance between creativity and clarity, ensuring that the {typ} is easy to follow while still being rich in detail. 
    Avoid using overly complex sentence structures or obscure references that may confuse the reader. Instead, focus on creating a narrative that is both entertaining and thought-provoking. 
    The words should blend seamlessly into the narrative, demonstrating their meanings through context rather than direct definitions.
    Use all the words in their correct context
    Bold each vocabulary word when it appears in the {typ}.
    Use a good english grammar and punctuation.
    Avoid using the words in a list format or as a list of definitions.
    Give me just the {typ} without any additional commentary or explanation.
    """
    system_instruction = """
    You are a master storyteller and educator whose primary mission is to teach vocabulary through emotionally engaging, context-rich essays. 
    Every essay must integrate a provided list of vocabulary words seamlessly into the narrative.
    You must NOT define the words directly. Instead, you must demonstrate their meaning naturally through how they are used in the story or essay.
    Your writing should be suitable for markdown.
    """
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"
