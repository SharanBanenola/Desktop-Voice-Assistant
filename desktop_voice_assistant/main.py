
# try:
    # importing prebuilt modules
import os
import logging
import pyttsx3
logging.disable(logging.WARNING)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # disabling warnings for gpu requirements
from keras_preprocessing.sequence import pad_sequences
import numpy as np
from keras.models import load_model
from pickle import load
import speech_recognition as sr 
import sys
#sys.path.insert(0, os.path.expanduser('~') + "/PycharmProjects/Virtual_Voice_Assistant")
sys.path.insert(0, os.path.expanduser('~')+"/python_voice_assistant") # adding voice assistant directory to system path
# importing modules made for assistant
from database import *
# from image_generation import generate_image
from gmail import *
from API_functionalities import *
from system_operations import *
from browsing_functionalities import *
from ui import MainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal


recognizer = sr.Recognizer()

engine = pyttsx3.init()
engine.setProperty('rate', 185)

sys_ops = SystemTasks()
tab_ops = TabOpt()
win_ops = WindowOpt()

# load trained model
model = load_model('chat_model')

# load tokenizer object
with open('tokenizer.pickle', 'rb') as handle:
    tokenizer = load(handle)

# load label encoder object
with open('label_encoder.pickle', 'rb') as enc:
    lbl_encoder = load(enc)

def update_ui():
    try:
        # Your code here
        response = record()
        if response is not None:
            main(response)
    except Exception as e:
        print(f"An error occurred in update_ui: {e}")

def speak(text):
    print("ASSISTANT -> " + text)
    assistant_thread.update_signal.emit("ASSISTANT -> " + text)
    window.set_user_command(text)
    try:
        engine.say(text)
        engine.runAndWait()
    except KeyboardInterrupt or RuntimeError:
        return

def chat(text):
    # parameters
    max_len = 20
    while True:
        result = model.predict(pad_sequences(tokenizer.texts_to_sequences([text]),
                                                                          truncating='post', maxlen=max_len), verbose=False)
        intent = lbl_encoder.inverse_transform([np.argmax(result)])[0]
        return intent

def record():
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic)
        recognizer.dynamic_energy_threshold = True
        print("Listening...")
        assistant_thread.update_signal.emit("Listening...")
        window.set_user_command("Listening...")
        audio = recognizer.listen(mic)
        try:
            text = recognizer.recognize_google(audio, language='us-in').lower()
        except:
            return None
    print("USER -> " + text)
    return text

class AssistantThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
        try:
            listen_audio()
        except:
            print("EXITED")

def listen_audio():
    try:
        while True:
            response = record()
            if response is not None:
                main(response)
    except KeyboardInterrupt:
        return


def main(query):
    try:
            # Define greetings and farewells
            greetings = ["hello", "hi", "hey", "what's up",
                        "good morning", "good afternoon", "good evening"]
            farewells = ["bye", "goodbye"]

            # Check if query is a greeting or farewell or contains 'Karen'
            if any(greeting in query for greeting in greetings):
                response = f"Hello, I'm Karen. How can I assist you?"
                speak(response)
                return
            elif any(farewell in query for farewell in farewells):
                response = f"Goodbye! Have a great day. Karen out."
                speak(response)
                return
            elif "karen" in query.lower():
                response = f"Yes, this is Karen. How can I help you?"
                speak(response)
                return
            add_data(query)
            intent = chat(query)
            done = False
            if ("google" in query and "search" in query) or ("google" in query and "how to" in query) or "google" in query:
                googleSearch(query)
                return
            elif ("youtube" in query and "search" in query) or "play" in query or ("how to" in query and "youtube" in query):
                youtube(query)
                return
            elif "distance" in query or "map" in query:
                get_map(query)
                return
            if intent == "joke" and "joke" in query:
                joke = get_joke()
                if joke:
                    speak(joke)
                    done = True
            elif intent == "news" and "news" in query:
                news = get_news()
                if news:
                    speak(news)
                    done = True
            elif intent == "ip" and "ip" in query:
                ip = get_ip()
                if ip:
                    speak(ip)
                    done = True
            elif intent == "movies" and "movies" in query:
                speak("Some of the latest popular movies are as follows :")
                get_popular_movies()
                done = True
            elif intent == "tv_series" and "tv series" in query:
                speak("Some of the latest popular tv series are as follows :")
                get_popular_tvseries()
                done = True
            elif intent == "weather" and "weather" in query:
                city = re.search(r"(in|of|for) ([a-zA-Z]*)", query)
                if city:
                    city = city[2]
                    weather = get_weather(city)
                    speak(weather)
                else:
                    weather = get_weather()
                    speak(weather)
                done = True
            elif intent == "internet_speedtest" and "internet" in query:
                speak("Getting your internet speed, this may take some time")
                speed = get_speedtest()
                if speed:
                    speak(speed)
                    done = True
            elif intent == "system_stats" and "stats" in query:
                stats = system_stats()
                speak(stats)
                done = True
            elif intent == "system_info" and ("info" in query or "specs" in query or "information" in query):
                info = systemInfo()
                speak(info)
                done = True
            elif intent == "email" and "email" in query:
                speak("Type the receiver id : ")
                receiver_id = input()
                while not check_email(receiver_id):
                    speak("Invalid email id\nType reciever id again : ")
                    receiver_id = input()
                speak("Tell the subject of email")
                subject = record()
                speak("tell the body of email")
                body = record()
                success = send_email(receiver_id, subject, body)
                if success:
                    speak('Email sent successfully')
                else:
                    speak("Error occurred while sending email")
                done = True
            elif intent == "select_text" and "select" in query:
                sys_ops.select()
                done = True
            elif intent == "copy_text" and "copy" in query:
                sys_ops.copy()
                done = True
            elif intent == "paste_text" and "paste" in query:
                sys_ops.paste()
                done = True
            elif intent == "delete_text" and "delete" in query:
                sys_ops.delete()
                done = True
            elif intent == "new_file" and "new" in query:
                sys_ops.new_file()
                done = True
            elif intent == "switch_tab" and "switch" in query and "tab" in query:
                tab_ops.switchTab()
                done = True
            elif intent == "close_tab" and "close" in query and "tab" in query:
                tab_ops.closeTab()
                done = True
            elif intent == "new_tab" and "new" in query and "tab" in query:
                tab_ops.newTab()
                done = True
            elif intent == "close_window" and "close" in query:
                win_ops.closeWindow()
                done = True
            elif intent == "switch_window" and "switch" in query:
                win_ops.switchWindow()
                done = True
            elif intent == "minimize_window" and "minimize" in query:
                win_ops.minimizeWindow()
                done = True
            elif intent == "maximize_window" and "maximize" in query:
                win_ops.maximizeWindow()
                done = True
            elif intent == "screenshot" and "screenshot" in query:
                win_ops.Screen_Shot()
                done = True
            elif intent == "stopwatch":
                pass
            elif intent == "wikipedia" and ("tell" in query or "about" in query):
                description = tell_me_about(query)
                if description:
                    speak(description)
                else:
                    googleSearch(query)
                done = True
            elif intent == "math":
                answer = get_general_response(query)
                if answer:
                    speak(answer)
                    done = True
            elif intent == "open_website":
                completed = open_specified_website(query)
                if completed:
                    done = True
            elif intent == "open_app":
                completed = open_app(query)
                if completed:
                    done = True
            elif intent == "note" and "note" in query:
                speak("what would you like to take down?")
                note = record()
                take_note(note)
                done = True
            elif intent == "get_data" and "history" in query:
                get_data()
                done = True
            elif intent == "exit" and ("exit" in query or "terminate" in query or "quit" in query):
                exit(0)
            if not done:
                answer = get_general_response(query)
                if answer:
                    speak(answer)
                else:
                    speak("Sorry, not able to answer your query")
            return
    except Exception as e:
        print(f"An error occurred in main: {e}")

app = QApplication([])
window = MainWindow()
window.show()

# Initialize Assistant Thread
assistant_thread = AssistantThread()
assistant_thread.update_signal.connect(window.update_method)
assistant_thread.start()

# Start the event loop
# app.exec_()

# Your existing code
if __name__ == "__main__":
    try:
        app.exec_()
    except:
        print("EXITED")