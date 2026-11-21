
import os
import hashlib

import pyttsx3
import pygame
from gtts import gTTS


class Speech:
    def __init__(self, language="en"):
        self.language = language.lower()

        self.audio_folder = os.path.join(
            os.path.dirname(__file__), "audio"
        )

        self.mixer_initialized = False

        if self.language == "hi":
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()

                self.mixer_initialized = True

            except Exception as error:
                print("Hindi audio initialization error:", error)

    def speak(self, message):
        if not message:
            return

        if self.language == "en":
            self._speak_english(message)

        elif self.language == "hi":
            self._speak_hindi(message)

    # --------------------------------
    # English voice
    # --------------------------------

    def _speak_english(self, message):
        engine = None

        try:
            # Fresh engine for every alert
            engine = pyttsx3.init()

            engine.setProperty("rate", 155)
            engine.setProperty("volume", 1.0)

            engine.say(message)
            engine.runAndWait()

        except Exception as error:
            print("English speech error:", error)

        finally:
            if engine:
                try:
                    engine.stop()
                except Exception:
                    pass

                del engine

    # --------------------------------
    # Hindi voice
    # --------------------------------

    def _speak_hindi(self, message):

        filename = self._get_hindi_filename(message)

        # Generate missing audio automatically
        if not os.path.exists(filename):

            try:
                print("Generating missing Hindi audio:", message)

                audio = gTTS(
                    text=message,
                    lang="hi"
                )

                os.makedirs(
                    self.audio_folder,
                    exist_ok=True
                )

                audio.save(filename)

                print("Hindi audio generated successfully.")

            except Exception as error:
                print("Hindi audio generation error:", error)
                return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.mixer_initialized = True

            pygame.mixer.music.stop()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy():
                clock.tick(20)

        except Exception as error:
            print("Hindi speech error:", error)

            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    # --------------------------------
    # Audio filename
    # --------------------------------

    def _get_hindi_filename(self, message):

        filename = hashlib.md5(
            message.encode("utf-8")
        ).hexdigest()

        return os.path.join(
            self.audio_folder,
            filename + ".mp3"
        )

    # --------------------------------
    # Cleanup
    # --------------------------------

    def close(self):

        if self.language == "hi":

            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()

            except Exception as error:
                print("Audio cleanup error:", error)

        self.mixer_initialized = False
