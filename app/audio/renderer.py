"""
Speech Renderer and Prosody Engine.
Transforms SpeechIntent (text + emotion) into prosody-rich SAPI XML / SSML markup
with natural pauses, rhythm adjustments, and pronunciation optimization.
"""
from dataclasses import dataclass
import re
from typing import Dict, Optional

from .profiles import PetEmotion, EmotionVoiceProfile, VOICE_PROFILES


@dataclass
class SpeechIntent:
    """
    Represents an intended vocal utterance from the pet character.
    Decouples pet behavior from specific audio rendering engines.
    """
    text: str
    emotion: PetEmotion = PetEmotion.NEUTRAL
    priority: int = 50  # Higher value = higher priority (e.g. correct food = 100)


class SpeechRenderer:
    """
    Renders clean dialogue text into prosody-enhanced SAPI XML.
    Applies emotional prosody, pauses, pitch curves, and phonetic adjustments.
    """

    # Pronunciation dictionary for child-directed vocabulary clarity
    PRONUNCIATION_OVERRIDES: Dict[str, str] = {
        "rice_egg": "rice and egg",
        "fried_chicken": "fried chicken",
        "om-nom-nom": "om nom nom",
        "yippee": "yip-pee",
        "oopsie-daisy": "oopsie daisy",
        "tee-hee": "tee hee",
    }

    def __init__(self, profiles: Optional[Dict[PetEmotion, EmotionVoiceProfile]] = None):
        self.profiles = profiles or VOICE_PROFILES

    def render(self, intent: SpeechIntent) -> str:
        """
        Transforms a SpeechIntent into fully-formed SAPI XML markup.
        """
        profile = self.profiles.get(intent.emotion, self.profiles[PetEmotion.NEUTRAL])
        cleaned_text = self._prepare_text(intent.text)

        # Build SAPI XML prosody tags
        xml_parts = []

        # Optional prefix silence for thoughtful/sad/confused pauses
        if profile.prefix_pause_ms > 0:
            xml_parts.append(f'<silence msec="{profile.prefix_pause_ms}"/>')

        # Insert prosody wrapper
        # <pitch absmiddle="N"> adjusts pitch: +4 (gentle/sad) to +10 (excited/happy child)
        # <rate speed="N"> adjusts speed: -4 (sleepy) to 0 (excited)
        # <volume level="N"> adjusts loudness: 80 to 100
        body = self._inject_prosodic_pauses(cleaned_text, profile)

        xml = (
            f'<pitch absmiddle="{profile.pitch_delta}">'
            f'<rate speed="{profile.rate_speed}">'
            f'<volume level="{profile.volume_level}">'
            f'{body}'
            f'</volume>'
            f'</rate>'
            f'</pitch>'
        )
        xml_parts.append(xml)

        if profile.suffix_pause_ms > 0:
            xml_parts.append(f'<silence msec="{profile.suffix_pause_ms}"/>')

        return "".join(xml_parts)

    def _prepare_text(self, raw_text: str) -> str:
        """Applies pronunciation overrides and cleans XML entities."""
        text = raw_text.strip()

        # Apply pronunciation overrides
        for raw_word, spoken_word in self.PRONUNCIATION_OVERRIDES.items():
            pattern = re.compile(re.escape(raw_word), re.IGNORECASE)
            text = pattern.sub(spoken_word, text)

        # Escape XML entities
        text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        return text

    def _inject_prosodic_pauses(self, text: str, profile: EmotionVoiceProfile) -> str:
        """
        Replaces punctuation marks with expressive SAPI silence tags
        to prevent flat, monotone delivery and enforce natural child rhythm.
        """
        # Ellipsis "..." represents a thoughtful hesitation (220-350ms)
        pause_ellipsis = 300 if profile.rate_speed < 0 else 220
        text = re.sub(r'\.\.\.+', f'... <silence msec="{pause_ellipsis}"/> ', text)

        # Exclamation marks: short energetic pause (120-180ms)
        text = re.sub(r'!+', '! <silence msec="140"/> ', text)

        # Question marks: wondering pause (180-240ms)
        text = re.sub(r'\?+', '? <silence msec="200"/> ', text)

        # Commas: brief breathing pause (100-140ms)
        text = re.sub(r',', ', <silence msec="110"/> ', text)

        # Clean multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
