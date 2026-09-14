"""
Pet State Machine and Metrics.
Manages emotional state, hunger, happiness, energy levels, and pet desires.
"""
from enum import Enum
import time


class PetMood(Enum):
    HUNGRY = "HUNGRY"
    HAPPY = "HAPPY"
    SAD = "SAD"
    LONELY = "LONELY"
    SLEEPY = "SLEEPY"


class PetDesire(Enum):
    FOOD = "FOOD"
    AFFECTION = "AFFECTION"
    PLAY = "PLAY"
    SLEEP = "SLEEP"


class PetState:
    def __init__(
        self,
        initial_mood: PetMood = PetMood.HUNGRY,
        hunger: float = 72.0,
        happiness: float = 65.0,
        energy: float = 80.0,
    ):
        self._mood: PetMood = initial_mood
        self._hunger: float = float(hunger)
        self._happiness: float = float(happiness)
        self._energy: float = float(energy)
        self._time_since_interaction: float = 0.0
        self._time_since_affection: float = 0.0
        now = time.time()
        self._last_interaction_time: float = now
        self._last_affection_time: float = now

    @property
    def mood(self) -> PetMood:
        return self._mood

    @mood.setter
    def mood(self, new_mood: PetMood):
        self._mood = new_mood

    @property
    def hunger(self) -> float:
        return self._hunger

    @hunger.setter
    def hunger(self, val: float):
        self._hunger = max(0.0, min(100.0, float(val)))

    @property
    def happiness(self) -> float:
        return self._happiness

    @happiness.setter
    def happiness(self, val: float):
        self._happiness = max(0.0, min(100.0, float(val)))

    @property
    def energy(self) -> float:
        return self._energy

    @energy.setter
    def energy(self, val: float):
        self._energy = max(0.0, min(100.0, float(val)))

    @property
    def time_since_interaction(self) -> float:
        return self._time_since_interaction

    @property
    def time_since_affection(self) -> float:
        return self._time_since_affection

    @property
    def last_interaction_time(self) -> float:
        return self._last_interaction_time

    @property
    def last_affection_time(self) -> float:
        return self._last_affection_time

    @property
    def current_desire(self) -> PetDesire:
        """Determines pet's strongest desire based on physical and emotional needs."""
        if self._energy < 25.0:
            return PetDesire.SLEEP

        # 1. Primary physical need: Hunger takes precedence when hungry
        if self._hunger >= 50.0 or self._mood == PetMood.HUNGRY:
            return PetDesire.FOOD

        # 2. Emotional need: Affection when lonely or not petted in > 20s
        if self._mood == PetMood.LONELY or (self._time_since_affection > 20.0) or self._happiness < 50.0:
            return PetDesire.AFFECTION

        # 3. Otherwise desires to play and engage
        return PetDesire.PLAY

    def mark_interaction(self):
        self._time_since_interaction = 0.0
        self._last_interaction_time = time.time()

    def feed_success(self, hunger_delta: float = 30.0, happiness_delta: float = 20.0):
        """Called when correct food is provided."""
        self._hunger = max(0.0, min(100.0, self._hunger - hunger_delta))
        self._happiness = max(0.0, min(100.0, self._happiness + happiness_delta))
        self.mark_interaction()
        self._mood = PetMood.HAPPY

    def give_affection(self, happiness_boost: float = 20.0):
        """Called when user pets/strokes the pet or gives head pats."""
        self.happiness = self._happiness + happiness_boost
        self._time_since_affection = 0.0
        self._last_affection_time = time.time()
        self.mark_interaction()
        if self._mood in (PetMood.LONELY, PetMood.SAD):
            self._mood = PetMood.HAPPY

    def feed_wrong(self, happiness_delta: float = 5.0):
        """Called when wrong food is shown. Gentle, remains hungry."""
        self._happiness = max(0.0, min(100.0, self._happiness - happiness_delta))
        self.mark_interaction()
        # Remains HUNGRY as per PRD Section 14
        self._mood = PetMood.HUNGRY

    def update_passive(self, delta_time: float):
        """Subtle passive decay over time."""
        self._hunger = min(100.0, self._hunger + (delta_time * 0.15))
        self._energy = max(0.0, self._energy - (delta_time * 0.05))
        self._time_since_interaction += delta_time
        self._time_since_affection += delta_time

        # If not petted for > 20 seconds, happiness decays gradually
        if self._time_since_affection > 20.0:
            self._happiness = max(25.0, self._happiness - (delta_time * 0.25))

        # Harmonized passive mood transitions
        if self._energy < 25.0:
            self._mood = PetMood.SLEEPY
        elif self._hunger >= 50.0:
            self._mood = PetMood.HUNGRY
        elif self._time_since_affection > 20.0:
            self._mood = PetMood.LONELY


    def as_dict(self) -> dict:
        return {
            "mood": self._mood.value,
            "desire": self.current_desire.value,
            "hunger": round(self._hunger, 1),
            "happiness": round(self._happiness, 1),
            "energy": round(self._energy, 1),
        }
