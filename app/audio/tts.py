"""
Asynchronous, Thread-Safe Child-Like Pet TTS Service.
Supports Neural Child Voice (en-US-AnaNeural) via EdgeTTSChildProvider with disk caching,
with graceful offline fallback to Windows Native SAPI 5 (SAPITTSProvider) and pyttsx3.
"""
from abc import ABC, abstractmethod
import asyncio
import hashlib
import logging
from pathlib import Path
import queue
import threading
import time
from typing import Optional, Union

from .profiles import PetEmotion
from .renderer import SpeechIntent, SpeechRenderer

logger = logging.getLogger("pet.audio")


def _safe_print_speech(label: str, text: str, emotion: str = "NEUTRAL"):
    """Safely prints dialogue to console without failing on Windows charmap/cp1252."""
    try:
        print(f"\n>>> [{label} | {emotion}]: \"{text}\"")
    except Exception:
        try:
            safe = text.encode("ascii", errors="replace").decode("ascii")
            print(f"\n>>> [{label} | {emotion}]: \"{safe}\"")
        except Exception:
            pass


class TTSProvider(ABC):
    """Abstract interface for speech synthesis backends."""

    @abstractmethod
    def synthesize_and_play(self, intent: SpeechIntent, xml_markup: str):
        """Synthesizes and outputs the given speech markup."""
        pass

    @abstractmethod
    def stop(self):
        """Stops active audio playback."""
        pass


class MockTTSProvider(TTSProvider):
    """Logging-only fallback provider for headless testing."""

    def synthesize_and_play(self, intent: SpeechIntent, xml_markup: str):
        logger.info(f"[Mock TTS | {intent.emotion.value}]: {intent.text}")
        _safe_print_speech("PET SPEAKS (Mock)", intent.text, intent.emotion.value)

    def stop(self):
        pass


class EdgeTTSChildProvider(TTSProvider):
    """
    State-of-the-art Neural Child Voice Provider (en-US-AnaNeural).
    Generates genuine, expressive, lovable young child speech.
    Features persistent disk caching in data/audio_cache/ for 0-latency offline playback.
    """

    # Dynamic prosody tuning per emotion for child persona
    EMOTION_TUNING = {
        PetEmotion.NEUTRAL: {"rate": "+0%", "pitch": "+0Hz"},
        PetEmotion.HAPPY: {"rate": "+4%", "pitch": "+8Hz"},
        PetEmotion.EXCITED: {"rate": "+8%", "pitch": "+12Hz"},
        PetEmotion.SAD: {"rate": "-8%", "pitch": "-4Hz"},
        PetEmotion.LONELY: {"rate": "-8%", "pitch": "-3Hz"},
        PetEmotion.HUNGRY: {"rate": "-3%", "pitch": "+3Hz"},
        PetEmotion.CONFUSED: {"rate": "-3%", "pitch": "+4Hz"},
        PetEmotion.SURPRISED: {"rate": "+8%", "pitch": "+10Hz"},
        PetEmotion.SLEEPY: {"rate": "-14%", "pitch": "-6Hz"},
        PetEmotion.ENCOURAGING: {"rate": "+4%", "pitch": "+6Hz"},
    }

    def __init__(
        self,
        voice: str = "en-US-AnaNeural",
        cache_dir: Optional[Path] = None,
        fallback_provider: Optional[TTSProvider] = None,
    ):
        self.voice = voice
        self.cache_dir = cache_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "audio_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.fallback = fallback_provider or SAPITTSProvider()
        self._init_mixer()

    def _init_mixer(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            logger.warning(f"Failed to initialize pygame.mixer: {e}")

    def synthesize_and_play(self, intent: SpeechIntent, xml_markup: str):
        import pygame

        _safe_print_speech("PET SPEAKS (True Child Voice)", intent.text, intent.emotion.value)

        clean_text = intent.text.strip()
        tuning = self.EMOTION_TUNING.get(intent.emotion, {"rate": "+0%", "pitch": "+0Hz"})
        cache_key = hashlib.md5(f"{self.voice}_{intent.emotion.value}_{tuning['rate']}_{tuning['pitch']}_{clean_text}".encode("utf-8")).hexdigest()
        audio_file = self.cache_dir / f"{cache_key}.mp3"

        # 1. Synthesize if not in local disk cache
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            try:
                import edge_tts

                async def _download():
                    comm = edge_tts.Communicate(
                        text=clean_text,
                        voice=self.voice,
                        rate=tuning["rate"],
                        pitch=tuning["pitch"],
                    )
                    await comm.save(str(audio_file))

                asyncio.run(_download())
            except Exception as err:
                logger.warning(f"edge_tts network fetch failed ({err}), using SAPI fallback...")
                if self.fallback:
                    self.fallback.synthesize_and_play(intent, xml_markup)
                return

        # 2. Instant playback of cached audio
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            sound = pygame.mixer.Sound(str(audio_file))
            channel = sound.play()
            if channel:
                while channel.get_busy():
                    time.sleep(0.04)
            else:
                pygame.mixer.music.load(str(audio_file))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.04)
        except Exception as play_err:
            logger.error(f"Playback error: {play_err}")
            if self.fallback:
                self.fallback.synthesize_and_play(intent, xml_markup)

    def stop(self):
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.stop()
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
        except Exception:
            pass


class SAPITTSProvider(TTSProvider):
    """
    Windows Native SAPI 5 Provider with Child-Voice Pitch Modulation.
    Runs inside a dedicated STA COM apartment thread with CoInitialize/CoUninitialize.
    Interprets SAPI XML prosody tags (<pitch>, <rate>, <volume>, <silence>).
    """

    def __init__(self):
        self._speaker = None
        self._init_speaker()

    def _init_speaker(self):
        try:
            import comtypes
            import comtypes.client
            comtypes.CoInitialize()

            self._speaker = comtypes.client.CreateObject("SAPI.SpVoice")

            voices = self._speaker.GetVoices()
            for i in range(voices.Count):
                v = voices.Item(i)
                desc = v.GetDescription().lower()
                if "zira" in desc or "female" in desc or "en-us" in desc:
                    self._speaker.Voice = v
                    logger.info(f"SAPI TTS initialized with voice: {v.GetDescription()}")
                    break
        except Exception as e:
            logger.error(f"Failed to initialize SAPI.SpVoice: {e}")
            self._speaker = None

    def synthesize_and_play(self, intent: SpeechIntent, xml_markup: str):
        if not self._speaker:
            self._init_speaker()

        _safe_print_speech("PET SPEAKS (SAPI Fallback)", intent.text, intent.emotion.value)

        if self._speaker:
            try:
                self._speaker.Speak(xml_markup, 8)
            except Exception as err:
                logger.warning(f"SAPI XML speak failed ({err}), falling back to plain text...")
                try:
                    self._speaker.Speak(intent.text, 0)
                except Exception as plain_err:
                    logger.error(f"SAPI plain text speak failed: {plain_err}")
        else:
            time.sleep(1.0)

    def stop(self):
        if self._speaker:
            try:
                self._speaker.Speak("", 2)
            except Exception:
                pass


class Pyttsx3Provider(TTSProvider):
    """Fallback provider using pyttsx3 when native SAPI comtypes is unavailable."""

    def __init__(self):
        self._engine = None
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "female" in v.name.lower():
                    self._engine.setProperty("voice", v.id)
                    break
        except Exception as e:
            logger.error(f"pyttsx3 initialization failed: {e}")

    def synthesize_and_play(self, intent: SpeechIntent, xml_markup: str):
        _safe_print_speech("PET SPEAKS (pyttsx3)", intent.text, intent.emotion.value)
        if self._engine:
            try:
                self._engine.say(intent.text)
                self._engine.runAndWait()
            except Exception as e:
                logger.error(f"pyttsx3 speech error: {e}")
        else:
            time.sleep(1.0)

    def stop(self):
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass


class TTSService:
    """
    Facade managing the complete Pet Voice Subsystem:
    - Compiles SpeechIntent using SpeechRenderer into expressive prosody markup.
    - Manages an asynchronous worker thread.
    - Prevents overlapping audio and filters duplicate/stale speech intents.
    """

    def __init__(
        self,
        provider: TTSProvider,
        renderer: Optional[SpeechRenderer] = None,
        max_queue_size: int = 3,
        duplicate_window_sec: float = 1.8,
    ):
        self.provider = provider
        self.renderer = renderer or SpeechRenderer()
        self.max_queue_size = max_queue_size
        self.duplicate_window_sec = duplicate_window_sec

        self._queue = queue.Queue()
        self._running = True
        self._is_active_speaking = False
        self._last_spoken_text = ""
        self._last_spoken_time = 0.0

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="PetVoiceWorkerThread",
        )
        self._worker_thread.start()

    def _worker_loop(self):
        """Worker thread processing queued speech intents sequentially."""
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass

        while self._running:
            try:
                item = self._queue.get(timeout=0.1)
                if item is None:  # Shutdown sentinel
                    break

                intent, xml_markup = item
                self._is_active_speaking = True

                self.provider.synthesize_and_play(intent, xml_markup)

                self._is_active_speaking = False
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Voice worker exception: {e}")
                self._is_active_speaking = False

        try:
            import comtypes
            comtypes.CoUninitialize()
        except Exception:
            pass

    def speak(
        self,
        intent_or_text: Union[SpeechIntent, str],
        emotion: PetEmotion = PetEmotion.NEUTRAL,
        priority: int = 50,
    ):
        """
        Submits an utterance to the speech queue.
        Supports both SpeechIntent objects and legacy plain text strings.
        """
        if not self._running:
            return

        if isinstance(intent_or_text, str):
            intent = SpeechIntent(text=intent_or_text, emotion=emotion, priority=priority)
        else:
            intent = intent_or_text

        # 1. Duplicate & Rapid-Fire Prevention (PRD Section 18 & 19)
        now = time.time()
        normalized_text = intent.text.strip().lower()
        if (
            normalized_text == self._last_spoken_text.lower()
            and (now - self._last_spoken_time) < self.duplicate_window_sec
        ):
            logger.debug(f"Suppressing duplicate speech: '{intent.text}'")
            return

        # 2. Queue Capacity Control
        if self._queue.qsize() >= self.max_queue_size:
            logger.debug(f"Queue full ({self._queue.qsize()}), dropping low-priority speech: '{intent.text}'")
            return

        # 3. Compile Prosody Markup via SpeechRenderer
        xml_markup = self.renderer.render(intent)

        # 4. Update tracking and enqueue
        self._last_spoken_text = intent.text
        self._last_spoken_time = now
        self._queue.put((intent, xml_markup))

    def is_speaking(self) -> bool:
        """Returns True if the pet is actively speaking or speech is queued."""
        return self._is_active_speaking or not self._queue.empty()

    def stop(self):
        """Stops playback and shuts down worker thread cleanly."""
        self._running = False
        self._queue.put(None)
        self.provider.stop()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)


def create_tts_service(
    enabled: bool = True,
    provider_name: str = "neural_child",
) -> TTSService:
    """Factory creating configured TTSService instance."""
    if not enabled:
        return TTSService(provider=MockTTSProvider())

    # Priority 1: Neural Child Voice (Microsoft Ana - authentic young child)
    if provider_name.lower() in ("neural_child", "edge", "child", "auto"):
        try:
            import edge_tts
            logger.info("Initializing EdgeTTSChildProvider (en-US-AnaNeural - True Child Voice)...")
            return TTSService(provider=EdgeTTSChildProvider())
        except Exception as e:
            logger.warning(f"EdgeTTSChildProvider unavailable ({e}), falling back to SAPI...")

    # Priority 2: Windows Native SAPI
    if provider_name.lower() in ("sapi", "auto", "neural_child"):
        try:
            import comtypes
            import comtypes.client
            comtypes.CoInitialize()
            test_obj = comtypes.client.CreateObject("SAPI.SpVoice")
            comtypes.CoUninitialize()
            logger.info("Initializing SAPITTSProvider for fallback Child Voice...")
            return TTSService(provider=SAPITTSProvider())
        except Exception as e:
            logger.warning(f"SAPI COM failed ({e}), falling back to pyttsx3...")

    # Priority 3: pyttsx3 fallback
    try:
        import pyttsx3
        return TTSService(provider=Pyttsx3Provider())
    except Exception:
        logger.warning("pyttsx3 unavailable, falling back to MockTTSProvider")
        return TTSService(provider=MockTTSProvider())
