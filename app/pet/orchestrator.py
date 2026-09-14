"""
Emotion and Audio-Visual Synchronization Orchestrator.
Coordinates shared emotion events across the 60 FPS Eye Renderer,
the Dashboard UI, and the Child-Like TTS Voice Subsystem.
Implements PRD Section 20 (VOICE_START_DELAY = 0.1s) and Section 21 (Shared Emotion Event).
"""
import logging
import threading
import time
from typing import Optional

from ..audio.profiles import PetEmotion
from ..audio.renderer import SpeechIntent
from ..audio.tts import TTSService
from ..eyes.events import EyeEvent
from ..eyes.renderer import EyeRenderer
from ..eyes.states import EyeState

logger = logging.getLogger("pet.orchestrator")


class EmotionOrchestrator:
    """
    Coordinates shared emotional expressions across both Visual (Eyes) and Vocal (TTS) channels.
    Ensures eye animations trigger first, followed by a slight (0.1s) synchronization delay
    before vocal speech begins, mimicking living animal reactions.
    """

    # Mapping PetEmotion to default EyeEvents for temporary reactions
    EMOTION_TO_EYE_EVENT = {
        PetEmotion.HAPPY: EyeEvent.CORRECT_FOOD,
        PetEmotion.EXCITED: EyeEvent.CORRECT_FOOD,
        PetEmotion.CONFUSED: EyeEvent.WRONG_FOOD,
        PetEmotion.SAD: EyeEvent.WRONG_FOOD,
        PetEmotion.SURPRISED: EyeEvent.FOOD_DETECTED,
        PetEmotion.NEUTRAL: EyeEvent.STARTUP,
    }

    # Mapping PetEmotion to persistent EyeStates
    EMOTION_TO_EYE_STATE = {
        PetEmotion.HAPPY: EyeState.HAPPY,
        PetEmotion.EXCITED: EyeState.HAPPY,
        PetEmotion.HUNGRY: EyeState.HUNGRY,
        PetEmotion.SAD: EyeState.SAD,
        PetEmotion.LONELY: EyeState.LONELY,
        PetEmotion.SURPRISED: EyeState.SURPRISED,
        PetEmotion.SLEEPY: EyeState.SLEEPY,
        PetEmotion.CONFUSED: EyeState.CONFUSED,
        PetEmotion.NEUTRAL: EyeState.IDLE,
        PetEmotion.ENCOURAGING: EyeState.HAPPY,
    }

    def __init__(
        self,
        eye_renderer: EyeRenderer,
        tts_service: TTSService,
        voice_start_delay: float = 0.1,
    ):
        self.eye_renderer = eye_renderer
        self.tts = tts_service
        self.voice_start_delay = voice_start_delay

    def emit_emotion(
        self,
        emotion: PetEmotion,
        message: str,
        eye_event: Optional[EyeEvent] = None,
        dashboard = None,
        speech_duration: float = 3.5,
        priority: int = 50,
    ):
        """
        Emits a coordinated emotion event:
        1. Visual reaction (Eye Animation) triggers immediately.
        2. Dashboard speech bubble and event log updated.
        3. Vocal reaction (TTS) begins after VOICE_START_DELAY (0.1s).
        """
        # 1. Trigger Visual Eye Animation
        selected_event = eye_event or self.EMOTION_TO_EYE_EVENT.get(emotion)
        if selected_event:
            self.eye_renderer.trigger_event(selected_event)
        else:
            persistent_state = self.EMOTION_TO_EYE_STATE.get(emotion, EyeState.IDLE)
            self.eye_renderer.set_persistent_state(persistent_state)

        # 2. Update UI Dashboard
        if dashboard:
            dashboard.set_speech(message, duration=speech_duration)
            dashboard.log_event(f"Pet ({emotion.value}): \"{message}\"")

        # 3. Dispatch Vocal Speech with synchronization delay
        intent = SpeechIntent(text=message, emotion=emotion, priority=priority)

        if self.voice_start_delay > 0:
            def _delayed_speech():
                time.sleep(self.voice_start_delay)
                self.tts.speak(intent)

            timer = threading.Thread(target=_delayed_speech, daemon=True, name="SyncVoiceTimer")
            timer.start()
        else:
            self.tts.speak(intent)
