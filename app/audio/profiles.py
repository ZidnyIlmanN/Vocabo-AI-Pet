"""
Pet Voice and Emotion Profiles.
Defines emotions, prosody parameters, and pitch/speed presets tailored
for a cute, young, friendly child-directed virtual pet character.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class PetEmotion(Enum):
    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    EXCITED = "EXCITED"
    SAD = "SAD"
    LONELY = "LONELY"
    HUNGRY = "HUNGRY"
    CONFUSED = "CONFUSED"
    SURPRISED = "SURPRISED"
    SLEEPY = "SLEEPY"
    ENCOURAGING = "ENCOURAGING"


@dataclass
class EmotionVoiceProfile:
    """
    Prosody parameters for a specific pet emotion.
    - pitch_delta: SAPI XML pitch modulation (-10 to +10). Positive values give youthful/child character tone.
    - rate_speed: SAPI XML rate (-10 to +10). Mapped to target 135-165 WPM for children.
    - volume_level: SAPI XML volume (0 to 100).
    - prefix_pause_ms: Pause before sentence start (in milliseconds).
    - suffix_pause_ms: Pause after sentence end.
    - pitch_contour: Stylistic pitch movement hint ('upward', 'downward', 'dynamic', 'flat').
    - description: Human-readable voice characteristic.
    """
    pitch_delta: int
    rate_speed: int
    volume_level: int = 100
    prefix_pause_ms: int = 0
    suffix_pause_ms: int = 200
    pitch_contour: str = "dynamic"
    description: str = ""


# Tuned profiles for all 10 required PRD emotions
# Ensures consistent child persona (same base character) while emoting naturally
VOICE_PROFILES: Dict[PetEmotion, EmotionVoiceProfile] = {
    PetEmotion.NEUTRAL: EmotionVoiceProfile(
        pitch_delta=7,
        rate_speed=-2,        # ~145 WPM (optimal child comprehension)
        volume_level=95,
        prefix_pause_ms=50,
        pitch_contour="dynamic",
        description="Friendly, youthful, clear and warm.",
    ),
    PetEmotion.HAPPY: EmotionVoiceProfile(
        pitch_delta=9,
        rate_speed=-1,        # ~155 WPM (bright and cheerful)
        volume_level=100,
        prefix_pause_ms=0,
        pitch_contour="upward",
        description="Energetic, higher pitch with upward intonation and cheerful bounce.",
    ),
    PetEmotion.EXCITED: EmotionVoiceProfile(
        pitch_delta=10,
        rate_speed=0,         # ~165 WPM (lively excitement)
        volume_level=100,
        prefix_pause_ms=0,
        pitch_contour="upward",
        description="High energy, noticeable pitch rise, enthusiastic and bright.",
    ),
    PetEmotion.SAD: EmotionVoiceProfile(
        pitch_delta=4,
        rate_speed=-3,        # ~135 WPM (gentle and subdued)
        volume_level=85,
        prefix_pause_ms=150,
        pitch_contour="downward",
        description="Slightly lower pitch, softer, slower with gentle downward intonation.",
    ),
    PetEmotion.LONELY: EmotionVoiceProfile(
        pitch_delta=5,
        rate_speed=-3,        # ~135 WPM (soft and sweet)
        volume_level=85,
        prefix_pause_ms=200,
        pitch_contour="downward",
        description="Soft, slightly sad, emotionally expressive, yearning for companionship.",
    ),
    PetEmotion.HUNGRY: EmotionVoiceProfile(
        pitch_delta=7,
        rate_speed=-2,        # ~145 WPM (gentle and longing)
        volume_level=90,
        prefix_pause_ms=100,
        pitch_contour="dynamic",
        description="Slightly soft, gentle, moderate speed with warm begging tone.",
    ),
    PetEmotion.CONFUSED: EmotionVoiceProfile(
        pitch_delta=7,
        rate_speed=-2,        # ~145 WPM (thoughtful with pause)
        volume_level=90,
        prefix_pause_ms=150,
        pitch_contour="dynamic",
        description="Thoughtful pause at beginning, gentle correction, encouraging tone.",
    ),
    PetEmotion.SURPRISED: EmotionVoiceProfile(
        pitch_delta=10,
        rate_speed=0,         # ~165 WPM (quick reaction)
        volume_level=100,
        prefix_pause_ms=0,
        pitch_contour="upward",
        description="Quick pitch rise, high energy, enthusiastic gasp.",
    ),
    PetEmotion.SLEEPY: EmotionVoiceProfile(
        pitch_delta=4,
        rate_speed=-4,        # ~125 WPM (slow, relaxed drowsy pace)
        volume_level=80,
        prefix_pause_ms=250,
        pitch_contour="downward",
        description="Slower, softer, lower energy, relaxed longer pauses.",
    ),
    PetEmotion.ENCOURAGING: EmotionVoiceProfile(
        pitch_delta=8,
        rate_speed=-1,        # ~150 WPM (motivating and warm)
        volume_level=98,
        prefix_pause_ms=50,
        pitch_contour="upward",
        description="Positive, warm, moderately energetic, very clear pronunciation.",
    ),
}
