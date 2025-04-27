import requests
from bs4 import BeautifulSoup as bs

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

def scrape_the_word(wrd:str) -> tuple[list[str], list[str]]:
    word = wrd.replace(' ', '-')
    
    word = word.strip().lower()
    
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    response = session.get(url, headers=headers, verify=False, timeout=20)

    soup = bs(response.content, 'html.parser')

    definitions = [item.text.strip().strip(':') for item in soup.find_all('div', class_='def ddef_d db')]
    examples = [item.text.strip() for item in soup.find_all('div', class_='examp dexamp')]
    
    return definitions, examples


# def scrape_tureng_turkish(wrd:str) -> list[str]:
#     word = wrd.replace(' ', '-')
    
#     word = word.strip().lower()
    
#     url = f"https://tureng.com/tr/turkce-ingilizce/{word}"
#     response = session.get(url, headers=headers, verify=True, timeout=20)
#     response.encoding = 'utf-8'
#     soup = bs(response.content, 'html.parser')

#     turkish_meanings = [item.text.strip() for item in soup.find_all('td', class_='tr ts')]
#     print(response.status_code) 403
#     return turkish_meanings[:5]


def scrape_turkish_meaning(wrd:str) -> list[str]:
    word = wrd.replace(' ', '-')
    
    word = word.strip().lower()
    
    url = f"https://dictionary.cambridge.org/dictionary/english-turkish/{word}"
    response = session.get(url, headers=headers, verify=True, timeout=20)
    response.encoding = 'utf-8'
    
    soup = bs(response.content, 'html.parser')

    turkish_meanings = [item.text.strip() for item in soup.find_all('span', class_='trans dtrans dtrans-se')]
    return turkish_meanings