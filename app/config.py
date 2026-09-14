"""
Central Configuration for Interactive AI Pet Prototype.
Loads environment variables with fallback defaults.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CATALOG_PATH = DATA_DIR / "food_catalog.json"
MODELS_DIR = ROOT_DIR / "models"
LOGS_DIR = ROOT_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load optional .env file
load_dotenv(ROOT_DIR / ".env")


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class AppConfig:
    # Vision & Detection
    confidence_threshold: float = field(
        default_factory=lambda: _get_float("CONFIDENCE_THRESHOLD", 0.65)
    )
    required_consecutive_frames: int = field(
        default_factory=lambda: _get_int("REQUIRED_CONSECUTIVE_FRAMES", 3)
    )
    camera_index: int = field(
        default_factory=lambda: _get_int("CAMERA_INDEX", 0)
    )
    camera_width: int = field(
        default_factory=lambda: _get_int("CAMERA_WIDTH", 640)
    )
    camera_height: int = field(
        default_factory=lambda: _get_int("CAMERA_HEIGHT", 480)
    )
    model_path: str = field(
        default_factory=lambda: os.getenv("MODEL_PATH", str(MODELS_DIR / "best.pt"))
    )
    fallback_to_mock_if_no_model: bool = field(
        default_factory=lambda: _get_bool("FALLBACK_TO_MOCK_IF_NO_MODEL", True)
    )

    # Behavior & Pet Timing
    response_cooldown_seconds: float = field(
        default_factory=lambda: _get_float("RESPONSE_COOLDOWN_SECONDS", 3.0)
    )
    initial_hunger: float = field(
        default_factory=lambda: _get_float("INITIAL_HUNGER", 72.0)
    )
    initial_happiness: float = field(
        default_factory=lambda: _get_float("INITIAL_HAPPINESS", 65.0)
    )
    initial_energy: float = field(
        default_factory=lambda: _get_float("INITIAL_ENERGY", 80.0)
    )

    # UI & Display
    window_width: int = field(
        default_factory=lambda: _get_int("WINDOW_WIDTH", 1024)
    )
    window_height: int = field(
        default_factory=lambda: _get_int("WINDOW_HEIGHT", 768)
    )
    fps: int = field(
        default_factory=lambda: _get_int("FPS", 60)
    )

    # Eye Animation
    blink_min_interval: float = field(
        default_factory=lambda: _get_float("BLINK_MIN_INTERVAL", 2.5)
    )
    blink_max_interval: float = field(
        default_factory=lambda: _get_float("BLINK_MAX_INTERVAL", 6.0)
    )
    eye_micro_motion_enabled: bool = field(
        default_factory=lambda: _get_bool("EYE_MICRO_MOTION_ENABLED", True)
    )
    eye_micro_motion_intensity: float = field(
        default_factory=lambda: _get_float("EYE_MICRO_MOTION_INTENSITY", 0.12)
    )
    eye_gaze_range_x: float = field(
        default_factory=lambda: _get_float("EYE_GAZE_RANGE_X", 12.0)
    )
    eye_gaze_range_y: float = field(
        default_factory=lambda: _get_float("EYE_GAZE_RANGE_Y", 8.0)
    )
    eye_expression_transition_duration: float = field(
        default_factory=lambda: _get_float("EYE_EXPRESSION_TRANSITION_DURATION", 0.28)
    )


    # Audio / TTS
    enable_tts: bool = field(
        default_factory=lambda: _get_bool("ENABLE_TTS", True)
    )
    voice_provider: str = field(
        default_factory=lambda: os.getenv("VOICE_PROVIDER", "neural_child")
    )
    voice_start_delay: float = field(
        default_factory=lambda: _get_float("VOICE_START_DELAY", 0.1)
    )
    tts_rate: int = field(
        default_factory=lambda: _get_int("TTS_RATE", 2)
    )
    tts_volume: float = field(
        default_factory=lambda: _get_float("TTS_VOLUME", 1.0)
    )
    tts_pitch: int = field(
        default_factory=lambda: _get_int("TTS_PITCH", 9)
    )


# Singleton instance
config = AppConfig()
