import json
import time
import pyttsx3
import pyaudio
import vosk
import requests
import webbrowser

class Speech:
    def __init__(self):
        self.tts = pyttsx3.init()

    def set_voice(self, speaker):
        voices = self.tts.getProperty('voices')
        return voices[speaker].id if speaker < len(voices) else voices[0].id

    def speak(self, text, speaker=0):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()
        time.sleep(0.1)

class Recognize:
    def __init__(self):
        model = vosk.Model('model_small')
        self.recognizer = vosk.KaldiRecognizer(model, 16000)
        self.start_audio_stream()

    def start_audio_stream(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=8000)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result['text']:
                    yield result['text']

last_lookup = {}

def fetch_word_info(word):
    global last_lookup
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url)
        response.raise_for_status()
        entry = response.json()[0]
        meanings = entry["meanings"]
        last_lookup = {
            "word": word,
            "meanings": meanings,
            "link": f"https://dictionaryapi.dev/"
        }
        return True
    except Exception:
        return False

def handle_command(command, speaker):
    global last_lookup

    if command.startswith("find "):
        word = command.split(" ", 1)[1]
        speaker.speak(f"Looking up the word {word}. Please wait.")
        if fetch_word_info(word):
            speaker.speak(f"I found information about {word}. You can ask for meaning, example, or save it.")
        else:
            speaker.speak("Sorry, I could not find that word.")

    elif "meaning" in command:
        if last_lookup:
            word = last_lookup["word"]
            text = f"Meanings for {word}: "
            for meaning in last_lookup["meanings"]:
                part = meaning["partOfSpeech"]
                definition = meaning["definitions"][0]["definition"]
                text += f"{part}: {definition}. "
            speaker.speak(text)
        else:
            speaker.speak("Please find a word first using the find command.")

    elif "example" in command:
        if last_lookup:
            examples = []
            for meaning in last_lookup["meanings"]:
                for defn in meaning["definitions"]:
                    if "example" in defn:
                        examples.append(defn["example"])
            if examples:
                for ex in examples[:2]:
                    speaker.speak(f"Example: {ex}")
            else:
                speaker.speak("Sorry, I couldn't find any examples.")
        else:
            speaker.speak("Please find a word first using the find command.")

    elif "save" in command:
        if last_lookup:
            with open("dictionary_log.txt", "a", encoding="utf-8") as f:
                f.write(f"Word: {last_lookup['word']}\n")
                for meaning in last_lookup["meanings"]:
                    f.write(f"  Part of Speech: {meaning['partOfSpeech']}\n")
                    for i, d in enumerate(meaning["definitions"]):
                        f.write(f"    {i+1}. {d['definition']}\n")
                        if 'example' in d:
                            f.write(f"       Example: {d['example']}\n")
                f.write("\n")
            speaker.speak("Word information saved to file.")
        else:
            speaker.speak("No word to save. Please use the find command first.")

    elif "link" in command:
        if last_lookup:
            webbrowser.open(last_lookup["link"])
            speaker.speak("Opening the dictionary link in browser.")
        else:
            speaker.speak("Please find a word first before opening the link.")

    else:
        speaker.speak("Sorry, I didn't understand that command.")

speech = Speech()
recognizer = Recognize()

speech.speak("Hello! I am your dictionary assistant. Say 'find' followed by a word to begin.")

for command_text in recognizer.listen():
    print("Heard:", command_text)
    if "exit" in command_text or "close" in command_text:
        speech.speak("Goodbye! I’ll be here when you need me.")
        break
    else:
        handle_command(command_text, speech)
