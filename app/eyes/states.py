"""
Eye States representing persistent emotional states.
"""
from enum import Enum


class EyeState(Enum):
    IDLE = "IDLE"
    HAPPY = "HAPPY"
    HUNGRY = "HUNGRY"
    SAD = "SAD"
    LONELY = "LONELY"
    SURPRISED = "SURPRISED"
    SLEEPY = "SLEEPY"
    CONFUSED = "CONFUSED"
