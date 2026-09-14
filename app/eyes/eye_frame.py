"""
EyeFrame — Composited Animation State.
Pure data structure representing the final computed eye appearance for one frame.
The renderer reads ONLY this — no animation logic, no timers.

PRD Section 18: Layered animation compositing.
  Base Expression + Gaze Offset + Micro Movement + Blink + Event Animation = Final EyeFrame
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .states import EyeState


@dataclass
class EyeFrame:
    """
    Complete snapshot of the eye animation state for a single render frame.
    Produced by EyeAnimationController.update(dt), consumed by EyeRenderer.render().
    """
    # ── Current Expression ────────────────────────────────────────────────
    state: EyeState = EyeState.IDLE
    prev_state: EyeState = EyeState.IDLE
    expression_progress: float = 1.0       # 0.0 = prev_state, 1.0 = current state

    # ── Eyelid / Blink ────────────────────────────────────────────────────
    eyelid_open: float = 1.0               # Global open fraction (0=closed, 1=open)
    left_openness_mod: float = 0.0         # Asymmetry modifier for left eye (±)
    right_openness_mod: float = 0.0        # Asymmetry modifier for right eye (±)

    # ── Gaze Offset ───────────────────────────────────────────────────────
    left_x_offset: float = 0.0             # Horizontal gaze offset (pixels)
    left_y_offset: float = 0.0             # Vertical gaze offset (pixels)
    right_x_offset: float = 0.0
    right_y_offset: float = 0.0

    # ── Pupil ─────────────────────────────────────────────────────────────
    pupil_scale: float = 1.0               # Pupil size multiplier

    # ── Expression Openness ───────────────────────────────────────────────
    expression_openness: float = 1.0       # From EXPRESSION_PROFILES

    # ── Body Motion ───────────────────────────────────────────────────────
    bounce_y: float = 0.0                  # Vertical bounce offset (pixels)
    squash_stretch: float = 1.0            # Vertical scale factor

    # ── Event Overlay ─────────────────────────────────────────────────────
    event_phase: str = "none"              # "none", "anticipation", "reaction", "settle"
    event_intensity: float = 0.0           # 0.0 to 1.0

    # ── Debug Info (togglable) ────────────────────────────────────────────
    blink_timer_remaining: float = 0.0
    gaze_target: Tuple[float, float] = (0.0, 0.0)
    current_animation: str = "idle"
    fps_animation: float = 60.0

    def effective_left_openness(self) -> float:
        """Final left eye openness combining all layers."""
        base = self.eyelid_open * self.expression_openness
        return max(0.0, min(1.0, base + self.left_openness_mod))

    def effective_right_openness(self) -> float:
        """Final right eye openness combining all layers."""
        base = self.eyelid_open * self.expression_openness
        return max(0.0, min(1.0, base + self.right_openness_mod))
