"""
Centralized Eye Animation Configuration.
All animation parameters in one place — no magic numbers scattered in code.
PRD Section 26: Configurable animation parameters.
"""
from .states import EyeState


# ──────────────────────────────────────────────────────────────────────────────
# Master Configuration Dictionary
# ──────────────────────────────────────────────────────────────────────────────
EYE_CONFIG = {
    # ── Blink System ──────────────────────────────────────────────────────
    "blink": {
        "min_interval": 2.5,          # Seconds between blinks (minimum)
        "max_interval": 6.0,          # Seconds between blinks (maximum)
        "normal_duration": 0.16,      # Normal blink duration (seconds)
        "short_duration": 0.12,       # Short/quick blink
        "long_duration": 0.22,        # Slightly longer blink
        "sleepy_duration": 0.35,      # Slow sleepy blink
        "double_blink_chance": 0.08,  # Probability of a double blink (8%)
        "short_blink_chance": 0.15,   # Probability of a short blink
        "long_blink_chance": 0.12,    # Probability of a longer blink
        "double_blink_gap": 0.18,     # Gap between double blinks (seconds)
        "post_surprise_cooldown": 0.8,  # No blink for 0.8s after SURPRISED
    },

    # ── Gaze System ───────────────────────────────────────────────────────
    "gaze": {
        "max_x": 12.0,               # Maximum horizontal gaze offset (pixels)
        "max_y": 8.0,                 # Maximum vertical gaze offset (pixels)
        "transition_speed": 5.5,      # Interpolation speed (higher = faster)
        "min_interval": 2.0,          # Min seconds between gaze changes
        "max_interval": 4.5,          # Max seconds between gaze changes
        "dead_zone": 2.5,             # Ignore new targets closer than this
        "min_movement": 3.0,          # Minimum distance for a gaze change
        # Weighted direction probabilities (must sum to 100)
        "direction_weights": {
            "center": 60,
            "left": 12,
            "right": 12,
            "up": 6,
            "down": 6,
            "diagonal": 4,
        },
    },

    # ── Expression Transition ─────────────────────────────────────────────
    "expression": {
        "transition_duration": 0.28,   # Seconds for smooth state transitions
        "min_hold_time": 0.5,          # Min time to stay in a new expression
    },

    # ── Micro Motion ──────────────────────────────────────────────────────
    "micro_motion": {
        "enabled": True,
        "intensity": 0.12,             # Subtle multiplier (0 = off, 1 = full)
        "min_interval": 4.0,           # Min seconds between micro-expressions
        "max_interval": 12.0,          # Max seconds between micro-expressions
        "pupil_scale_range": 0.04,     # Max pupil scale flutter (±4%)
        "asymmetry_range": 0.03,       # Max L/R eye openness asymmetry (±3%)
    },

    # ── Event Animation ───────────────────────────────────────────────────
    "event": {
        "anticipation_duration": 0.12,  # Pre-reaction subtle movement
        "settle_duration": 0.22,        # Post-reaction smooth return
    },

    # ── Idle Behavior ─────────────────────────────────────────────────────
    "idle": {
        "min_quiet_period": 1.5,       # Min seconds of stillness in idle
        "max_quiet_period": 5.0,       # Max seconds of stillness in idle
        "micro_expression_chance": 0.25,  # Chance of micro-expression after quiet
    },

    # ── Bounce (Happy state) ─────────────────────────────────────────────
    "bounce": {
        "amplitude": 6.0,             # Reduced from 12.0 for subtlety
        "frequency": 4.0,             # Slower than previous 6.0
        "squash_intensity": 0.04,     # Reduced from 0.08
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Per-Expression Profiles
# Each profile modifies the base eye parameters for its emotional state.
# ──────────────────────────────────────────────────────────────────────────────
EXPRESSION_PROFILES = {
    EyeState.IDLE: {
        "openness": 1.0,
        "pupil_scale": 1.0,
        "gaze_range": 1.0,           # Multiplier on gaze max_x/max_y
        "blink_speed": 1.0,          # Multiplier on blink duration
        "movement_speed": 1.0,       # Multiplier on gaze transition speed
        "micro_expression_prob": 0.2,
        "bounce_enabled": False,
    },
    EyeState.HAPPY: {
        "openness": 0.85,
        "pupil_scale": 1.0,
        "gaze_range": 0.4,           # Happy eyes mostly look forward
        "blink_speed": 0.85,         # Slightly quicker blinks
        "movement_speed": 1.2,
        "micro_expression_prob": 0.3,
        "bounce_enabled": True,
    },
    EyeState.HUNGRY: {
        "openness": 0.82,
        "pupil_scale": 1.0,
        "gaze_range": 0.6,
        "blink_speed": 1.0,
        "movement_speed": 0.8,       # Slower, pleading
        "micro_expression_prob": 0.15,
        "bounce_enabled": False,
    },
    EyeState.SAD: {
        "openness": 0.75,
        "pupil_scale": 0.92,
        "gaze_range": 0.5,
        "blink_speed": 1.2,          # Slightly slower blinks
        "movement_speed": 0.7,
        "micro_expression_prob": 0.1,
        "bounce_enabled": False,
    },
    EyeState.LONELY: {
        "openness": 0.80,
        "pupil_scale": 0.88,
        "gaze_range": 1.3,           # Looks around more when lonely
        "blink_speed": 1.1,
        "movement_speed": 0.6,
        "micro_expression_prob": 0.15,
        "bounce_enabled": False,
    },
    EyeState.SURPRISED: {
        "openness": 1.15,            # Slightly wider
        "pupil_scale": 1.12,         # Pupils slightly larger
        "gaze_range": 0.2,           # Focus forward
        "blink_speed": 1.0,
        "movement_speed": 1.5,       # Quick reaction
        "micro_expression_prob": 0.05,
        "bounce_enabled": False,
    },
    EyeState.SLEEPY: {
        "openness": 0.45,
        "pupil_scale": 0.90,
        "gaze_range": 0.3,
        "blink_speed": 2.2,          # Much slower blinks
        "movement_speed": 0.4,       # Very slow
        "micro_expression_prob": 0.05,
        "bounce_enabled": False,
    },
    EyeState.CONFUSED: {
        "openness": 0.90,
        "pupil_scale": 0.95,
        "gaze_range": 1.1,           # Darting gaze
        "blink_speed": 1.0,
        "movement_speed": 1.3,
        "micro_expression_prob": 0.2,
        "bounce_enabled": False,
    },
}


def get_profile(state: EyeState) -> dict:
    """Returns the expression profile for a given eye state, with IDLE as fallback."""
    return EXPRESSION_PROFILES.get(state, EXPRESSION_PROFILES[EyeState.IDLE])
