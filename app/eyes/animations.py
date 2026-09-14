"""
Eye Animation Geometry, Parametric Curves, and Easing Helpers.
Pure math and vector helpers for rendering cute digital pet expressions.
"""
import math
from typing import Tuple


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation clamped between 0 and 1."""
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    """Smooth cubic ease-in-out."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out_elastic(t: float) -> float:
    """Elastic overshoot easing for cheerful pops/bounces."""
    t = max(0.0, min(1.0, t))
    if t == 0:
        return 0.0
    if t == 1:
        return 1.0
    p = 0.3
    return math.pow(2, -10 * t) * math.sin((t - p / 4) * (2 * math.pi) / p) + 1.0


def calculate_blink_progress(elapsed_in_blink: float, duration: float) -> float:
    """
    Returns eyelid open fraction (1.0 = open, 0.0 = completely shut).
    Phase: 0 -> 0.5 (closing), 0.5 -> 1.0 (opening).
    """
    if duration <= 0:
        return 1.0
    t = max(0.0, min(1.0, elapsed_in_blink / duration))
    if t < 0.5:
        # Closing: 1.0 -> 0.0
        closing_t = t / 0.5
        return 1.0 - ease_in_out(closing_t)
    else:
        # Opening: 0.0 -> 1.0
        opening_t = (t - 0.5) / 0.5
        return ease_in_out(opening_t)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Hermite interpolation between edge0 and edge1."""
    if edge1 == edge0:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out deceleration."""
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3)


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in acceleration."""
    t = max(0.0, min(1.0, t))
    return t * t * t

