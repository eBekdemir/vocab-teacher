from gtts import gTTS
from io import BytesIO



def pronounce(text, slow=False, language='en'):
    tts = gTTS(text=text, lang=language, slow=slow)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file


def essay_pronounce(text, slow=False, language='en'): # TODO: it is too robotic, find another way to pronounce essays, also it takes too long to generate the audio file.
    text = text.replace('\n', ' ').replace('*', '').replace('_', '').replace('-', '')
    tts = gTTS(text=text, lang=language, slow=slow)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file