from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
open_router_api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=open_router_api_key
)

def generate_an_essay_with_words(vocab_words, theme=None, length="medium"):
    words_str = ", ".join(vocab_words)
    
    length_instructions = {
        "short": "Write a 1-paragraph story",
        "medium": "Write a 3-paragraph story",
        "long": "Write a 5-paragraph essay"
    }
    length_instruction = length_instructions.get(length, "medium")
    
    theme_instruction = f" about {theme}" if theme else ""
    
    prompt = f"""
    {length_instruction}{theme_instruction} that naturally incorporates the following vocabulary words: {words_str}.
    
    Requirements:
    1. Use all the words in their correct context
    2. Make the story engaging and appropriate for language learners
    3. Bold each vocabulary word when it first appears in the story
    4. Ensure the story is engaging and captures the reader's interest
    """
    
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "system", "content": "You are a helpful vocabulary teacher who creates engaging stories that help students learn passed words."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    vocabulary_list = ["ephemeral", "quintessential", "serendipity", "luminous", "resilient"]
    story = generate_an_essay_with_words(
        vocab_words=vocabulary_list,
        length="medium"
    )
    print(story)