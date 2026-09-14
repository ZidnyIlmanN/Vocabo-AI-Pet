"""
Eye Events and Priority Hierarchy.
Temporary event animations take precedence over persistent states.
"""
from enum import Enum
from typing import Dict


class EyeEvent(Enum):
    STARTUP = "STARTUP"
    CORRECT_FOOD = "CORRECT_FOOD"
    WRONG_FOOD = "WRONG_FOOD"
    FOOD_DETECTED = "FOOD_DETECTED"
    ERROR = "ERROR"


# Higher numeric value indicates higher animation priority
EVENT_PRIORITY: Dict[EyeEvent, int] = {
    EyeEvent.CORRECT_FOOD: 100,
    EyeEvent.WRONG_FOOD: 90,
    EyeEvent.FOOD_DETECTED: 70,
    EyeEvent.STARTUP: 60,
    EyeEvent.ERROR: 50,
}

# Duration in seconds for temporary event animations
EVENT_DURATIONS: Dict[EyeEvent, float] = {
    EyeEvent.CORRECT_FOOD: 2.8,
    EyeEvent.WRONG_FOOD: 2.2,
    EyeEvent.FOOD_DETECTED: 1.2,
    EyeEvent.STARTUP: 2.5,
    EyeEvent.ERROR: 1.5,
}
