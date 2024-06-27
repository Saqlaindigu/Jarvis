import os
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Get API keys from environment variables
newsapi = os.getenv("NEWS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()


def get_weather(city):
    """Fetch and speak the weather for a specified city."""
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            weather_description = data['weather'][0]['description']
            speak(f"The current temperature in {city} is {temp} degrees Celsius with {weather_description}.")
        else:
            speak("Failed to fetch weather data.")
    except Exception as e:
        logging.error(f"Error fetching weather data: {e}")
        speak("I'm sorry, I couldn't retrieve the weather information.")


async def ai_process(command):
    """Process command using OpenAI."""
    try:
        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Virtual assistant, skilled in general tasks like Alexa and Google cloud."},
                {"role": "user", "content": command}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in AI processing: {e}")
        return "I'm sorry, I couldn't process that command."

async def process_command(command):
    """Process the voice command."""
    try:
        if "open google" in command.lower():
            webbrowser.open("https://google.com")
        elif "open facebook" in command.lower():
            webbrowser.open("https://facebook.com")
        elif "open youtube" in command.lower():
            webbrowser.open("https://youtube.com")
        elif "open linkedin" in command.lower():
            webbrowser.open("https://linkedin.com")
        elif command.lower().startswith("play"):
            song = command.lower().split(" ")[1]
            link = musicLibrary.music.get(song)
            if link:
                webbrowser.open(link)
            else:
                speak(f"Song {song} not found in the music library.")
        elif "news" in command.lower():
            response = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                for article in articles:
                    speak(article['title'])
            else:
                speak("Failed to fetch news.")
        elif "weather" in command.lower():
            city = command.lower().split("weather in ")[1]
            get_weather(city)
        else:
            output = await ai_process(command)
            speak(output)
    except Exception as e:
        logging.error(f"Error processing command: {e}")
        speak("I'm sorry, something went wrong while processing your command.")

async def main():
    """Main function to initialize and handle commands."""
    speak("Initializing Jarvis...")
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                logging.info("Listening for wake word...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                word = recognizer.recognize_google(audio)
                if word.lower() == "jarvis":
                    speak("Yes")
                    with sr.Microphone() as source:
                        logging.info("Jarvis active, listening for command...")
                        audio = recognizer.listen(source)
                        command = recognizer.recognize_google(audio)
                        await process_command(command)
        except sr.UnknownValueError:
            logging.warning("Could not understand audio")
        except sr.RequestError as e:
            logging.error(f"Could not request results; {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
