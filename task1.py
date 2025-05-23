import json
import time
import pyttsx3
import pyaudio
import vosk
import requests
from PIL import Image
from io import BytesIO


class Speech:
    def __init__(self):
        self.speaker = 0
        self.tts = pyttsx3.init()

    def set_voice(self, speaker):
        voices = self.tts.getProperty('voices')
        return voices[speaker].id if speaker < len(voices) else voices[0].id

    def text2voice(self, speaker=0, text='Ready'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        self.tts.say(text)
        self.tts.runAndWait()
        time.sleep(0.1)


class Recognize:
    def __init__(self):
        model = vosk.Model('model_small')
        self.record = vosk.KaldiRecognizer(model, 16000)
        self.stream_audio()

    def stream_audio(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=8000)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data):
                result = json.loads(self.record.Result())
                if result['text']:
                    yield result['text']


def speak(text):
    speech = Speech()
    speech.text2voice(speaker=0, text=text)


current_image_url = None
current_image_data = None


def fetch_new_image():
    global current_image_url, current_image_data
    try:
        response = requests.get("https://dog.ceo/api/breeds/image/random")
        response.raise_for_status()
        data = response.json()
        current_image_url = data["message"]
        image_response = requests.get(current_image_url)
        current_image_data = Image.open(BytesIO(image_response.content))
        speak("New dog image loaded.")
    except Exception:
        speak("Failed to fetch dog image.")


def handle_command(command):
    global current_image_url, current_image_data

    if "показать" in command:
        if current_image_data:
            current_image_data.show()
            speak("Here is the image.")
        else:
            speak("No image loaded. Say 'следующая' to load one.")

    elif "следующая" in command:
        fetch_new_image()

    elif "сохранить" in command:
        if current_image_data:
            current_image_data.save("dog.jpg")
            speak("Dog image saved.")
        else:
            speak("Nothing to save.")

    elif "назвать породу" in command:
        if current_image_url:
            parts = current_image_url.split("/")
            breed_index = parts.index("breeds") + 1
            breed = parts[breed_index].replace("-", " ")
            speak(f"Breed: {breed}")
        else:
            speak("No image to analyze.")

    elif "разрешение" in command:
        if current_image_data:
            width, height = current_image_data.size
            speak(f"Image resolution is {width} by {height} pixels.")
        else:
            speak("No image available.")

    else:
        speak("Command not recognized.")


rec = Recognize()
speak("Привет! Я голосовой помощник. Говори команду.")
print("Assistant started. Say a command...")
text_gen = rec.listen()

for text in text_gen:
    print("Command:", text)
    if "выход" in text or "закрыть" in text:
        speak("До встречи!")
        break
    else:
        handle_command(text)
