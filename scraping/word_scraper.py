import requests
from bs4 import BeautifulSoup as bs
from config.settings import RETRY_DELAY, RETRY_LIMIT, LOG_FILE_PATH
import time
import logging

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

def scrape_the_word(wrd:str) -> tuple[list[str], list[str]]:
    word = wrd.replace(' ', '-')
    
    word = word.strip().lower()
    
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    for attempt in range(RETRY_LIMIT):
        try:
            response = session.get(url, headers=headers, verify=False, timeout=20)
            response.raise_for_status()
            soup = bs(response.content, 'html.parser')
            
            definitions = [item.text.strip().strip(':') for item in soup.find_all('div', class_='def ddef_d db')]
            examples = [item.text.strip() for item in soup.find_all('div', class_='examp dexamp')]            
            return definitions, examples

        except Exception as e:
            logger.error(f"Error occurred while scraping ({word}): {e}")
            time.sleep(RETRY_DELAY)
            if attempt == RETRY_LIMIT - 1:
                return [], []
    return [], []


def scrape_turkish_meaning(wrd:str) -> list[str]:
    word = wrd.replace(' ', '-')
    
    word = word.strip().lower()
    
    url = f"https://dictionary.cambridge.org/dictionary/english-turkish/{word}"
    
    for attempt in range(RETRY_LIMIT):
        try:
            response = session.get(url, headers=headers, verify=False, timeout=20)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = bs(response.content, 'html.parser')

            turkish_meanings = [item.text.strip() for item in soup.find_all('span', class_='trans dtrans dtrans-se')]
            return turkish_meanings

        except Exception as e:
            logger.error(f"Error occurred while scraping ({word}): {e}")
            time.sleep(RETRY_DELAY)
            if attempt == RETRY_LIMIT - 1:
                return []
    return []