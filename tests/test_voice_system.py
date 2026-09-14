"""
Unit Tests for Child-Like Pet Voice and Speech System.
Validates Emotion Profiles, SpeechRenderer, Duplicate Suppression, and Orchestrator.
"""
import time
import pytest

from app.audio.profiles import PetEmotion, VOICE_PROFILES
from app.audio.renderer import SpeechIntent, SpeechRenderer
from app.audio.tts import TTSService, MockTTSProvider
from app.eyes.events import EyeEvent
from app.eyes.renderer import EyeRenderer
from app.pet.orchestrator import EmotionOrchestrator


def test_all_10_emotion_profiles_exist():
    """Verify all 10 required PRD emotions are configured with valid ranges."""
    required_emotions = [
        PetEmotion.NEUTRAL,
        PetEmotion.HAPPY,
        PetEmotion.EXCITED,
        PetEmotion.SAD,
        PetEmotion.LONELY,
        PetEmotion.HUNGRY,
        PetEmotion.CONFUSED,
        PetEmotion.SURPRISED,
        PetEmotion.SLEEPY,
        PetEmotion.ENCOURAGING,
    ]
    for emo in required_emotions:
        assert emo in VOICE_PROFILES
        prof = VOICE_PROFILES[emo]
        # Child pitch must be positive (+1 to +10)
        assert 0 <= prof.pitch_delta <= 10
        # Child rate must be within safe comprehension speed (-5 to +2)
        assert -5 <= prof.rate_speed <= 2
        assert 0 < prof.volume_level <= 100


def test_speech_renderer_xml_compilation():
    """Verify SpeechRenderer generates proper SAPI XML with prosody tags."""
    renderer = SpeechRenderer()
    intent = SpeechIntent(text="Yay! You found it!", emotion=PetEmotion.HAPPY)
    xml = renderer.render(intent)

    # Must contain pitch, rate, volume, and silence tags
    prof = VOICE_PROFILES[PetEmotion.HAPPY]
    assert f'<pitch absmiddle="{prof.pitch_delta}">' in xml
    assert f'<rate speed="{prof.rate_speed}">' in xml
    assert f'<volume level="{prof.volume_level}">' in xml
    assert '<silence msec="140"/>' in xml  # Pause for exclamation mark
    assert "Yay!" in xml


def test_speech_renderer_xml_escaping():
    """Verify raw XML characters are properly escaped to prevent SAPI parser errors."""
    renderer = SpeechRenderer()
    intent = SpeechIntent(text="Rice & Egg <yummy> \"favorite\"", emotion=PetEmotion.NEUTRAL)
    xml = renderer.render(intent)

    assert "&amp;" in xml
    assert "&lt;" in xml
    assert "&gt;" in xml
    assert "&quot;" in xml


def test_tts_duplicate_suppression():
    """Verify rapid consecutive identical speech intents are suppressed."""
    mock_provider = MockTTSProvider()
    tts = TTSService(provider=mock_provider, duplicate_window_sec=1.5)

    # Speak same utterance rapidly
    tts.speak("Yay! That's my favorite!")
    first_qsize = tts._queue.qsize()

    # Immediate second call should be ignored as duplicate
    tts.speak("Yay! That's my favorite!")
    second_qsize = tts._queue.qsize()

    assert first_qsize == second_qsize

    # Different text should be accepted
    tts.speak("Something else!")
    third_qsize = tts._queue.qsize()
    assert third_qsize > second_qsize

    tts.stop()


def test_emotion_orchestrator_coordination():
    """Verify EmotionOrchestrator coordinates eye animations and speech with delay."""
    eye_renderer = EyeRenderer()
    mock_provider = MockTTSProvider()
    tts = TTSService(provider=mock_provider)

    orchestrator = EmotionOrchestrator(
        eye_renderer=eye_renderer,
        tts_service=tts,
        voice_start_delay=0.05,
    )

    # Emit happy emotion
    orchestrator.emit_emotion(
        emotion=PetEmotion.HAPPY,
        message="Yay! That's exactly what I wanted!",
        eye_event=EyeEvent.CORRECT_FOOD,
    )

    # Eye event should be triggered immediately
    assert eye_renderer.active_event == EyeEvent.CORRECT_FOOD

    # Wait for the voice start delay
    time.sleep(0.1)
    assert tts._last_spoken_text == "Yay! That's exactly what I wanted!"

    tts.stop()
