"""
Voice Engine Module - Handles speech recognition and text-to-speech
Cross-Linux compatible using configured audio system
"""

import speech_recognition as sr
import pyttsx3
import threading
import queue
from typing import Optional, Callable, List
from jarvis.logger import get_logger
import time

logger = get_logger(__name__)


class VoiceRecognizer:
    """
    Handles microphone input and speech-to-text conversion
    Uses Google Speech Recognition API (fallback to offline if needed)
    """

    def __init__(self, language: str = "en-US", timeout: float = 30.0):
        """
        Initialize voice recognizer
        
        Args:
            language: Language for recognition (default English US)
            timeout: Timeout for listening (seconds)
        """
        self.recognizer = sr.Recognizer()
        self.language = language
        self.timeout = timeout
        self.microphone = sr.Microphone()

        # Adjust recognizer settings for better accuracy
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True

    def listen(self) -> Optional[str]:
        """
        Listen to microphone input and convert to text
        
        Returns:
            Recognized text or None if error/timeout
        """
        try:
            logger.info("Listening for voice input...")
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=self.timeout)

            logger.info("Audio captured, converting to text...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"Recognized: {text}")
            return text

        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Voice recognition error: {e}")
            return None

    def detect_wake_word(self, text: str, wake_word: str = "hello jarvis") -> bool:
        """
        Detect wake word in recognized text
        
        Args:
            text: Recognized text
            wake_word: Wake word to detect
        
        Returns:
            True if wake word detected
        """
        if not text:
            return False

        return wake_word.lower() in text.lower()

    def get_microphone_devices(self) -> List[str]:
        """
        Get list of available microphone devices
        
        Returns:
            List of device names
        """
        try:
            devices = sr.Microphone.list_microphone_indexes()
            device_names = []
            for device_index in devices:
                try:
                    device_names.append(f"Device {device_index}")
                except Exception:
                    pass
            return device_names
        except Exception as e:
            logger.error(f"Error listing microphone devices: {e}")
            return []


class VoiceSynthesizer:
    """
    Handles text-to-speech conversion
    Uses pyttsx3 for offline, cross-platform support
    """

    def __init__(self, rate: int = 150, volume: float = 0.9):
        """
        Initialize voice synthesizer
        
        Args:
            rate: Speaking rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        self.speaking = False
        self._lock = threading.Lock()

    def speak(self, text: str, wait: bool = True) -> None:
        """
        Convert text to speech and play audio
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to finish
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid text for speech synthesis")
            return

        try:
            with self._lock:
                logger.info(f"Speaking: {text[:50]}...")
                self.speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.speaking = False
        except Exception as e:
            logger.error(f"Error in voice synthesis: {e}")
            self.speaking = False

    def speak_async(self, text: str) -> None:
        """
        Speak text asynchronously (non-blocking)
        
        Args:
            text: Text to speak
        """
        thread = threading.Thread(target=self.speak, args=(text, True))
        thread.daemon = True
        thread.start()

    def set_rate(self, rate: int) -> None:
        """Set speaking rate"""
        try:
            self.engine.setProperty('rate', rate)
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")

    def set_volume(self, volume: float) -> None:
        """Set volume level (0.0 to 1.0)"""
        try:
            if 0.0 <= volume <= 1.0:
                self.engine.setProperty('volume', volume)
        except Exception as e:
            logger.error(f"Error setting volume: {e}")

    def get_voices(self) -> List[str]:
        """
        Get list of available voices
        
        Returns:
            List of voice names
        """
        try:
            voices = self.engine.getProperty('voices')
            return [f"Voice {i}: {v.name}" for i, v in enumerate(voices)]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    def set_voice(self, voice_id: int = 0) -> None:
        """Set voice by ID"""
        try:
            voices = self.engine.getProperty('voices')
            if 0 <= voice_id < len(voices):
                self.engine.setProperty('voice', voices[voice_id].id)
        except Exception as e:
            logger.error(f"Error setting voice: {e}")


class VoiceController:
    """
    High-level voice control combining recognition and synthesis
    """

    def __init__(self, config: dict = None):
        """
        Initialize voice controller
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Setup recognizer
        audio_config = self.config.get('audio', {})
        self.recognizer = VoiceRecognizer(
            timeout=audio_config.get('timeout_seconds', 30)
        )

        # Setup synthesizer
        voice_config = self.config.get('voice', {})
        self.synthesizer = VoiceSynthesizer(
            rate=voice_config.get('rate', 150),
            volume=voice_config.get('volume', 0.9)
        )
        self.synthesizer.set_voice(voice_config.get('voice_id', 0))

        self.wake_word = audio_config.get('wake_word', 'hello jarvis')

    def listen_for_wake_word(self) -> bool:
        """
        Listen and check for wake word
        
        Returns:
            True if wake word detected
        """
        text = self.recognizer.listen()
        if not text:
            return False

        return self.recognizer.detect_wake_word(text, self.wake_word)

    def listen_for_command(self) -> Optional[str]:
        """
        Listen for command after wake word detected
        
        Returns:
            Recognized command text or None
        """
        self.synthesizer.speak("I'm listening")
        return self.recognizer.listen()

    def speak(self, text: str, wait: bool = True) -> None:
        """
        Speak text
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete
        """
        self.synthesizer.speak(text, wait=wait)

    def speak_async(self, text: str) -> None:
        """Speak text asynchronously"""
        self.synthesizer.speak_async(text)