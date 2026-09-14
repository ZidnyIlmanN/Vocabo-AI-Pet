"""Audio and TTS module for Child-Like Pet Voice System."""
from .profiles import PetEmotion, EmotionVoiceProfile, VOICE_PROFILES
from .renderer import SpeechIntent, SpeechRenderer
from .tts import TTSService, TTSProvider, SAPITTSProvider, Pyttsx3Provider, MockTTSProvider, create_tts_service

__all__ = [
    "PetEmotion",
    "EmotionVoiceProfile",
    "VOICE_PROFILES",
    "SpeechIntent",
    "SpeechRenderer",
    "TTSService",
    "TTSProvider",
    "SAPITTSProvider",
    "Pyttsx3Provider",
    "MockTTSProvider",
    "create_tts_service",
]
