import speech_recognition as sr

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recognize_speech(self, language='zh-CN'):
        with sr.Microphone() as source:
            try:
                print("Listening...")
                audio = self.recognizer.listen(source)
                query_text = self.recognizer.recognize_google(audio, language=language)
                return query_text
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None