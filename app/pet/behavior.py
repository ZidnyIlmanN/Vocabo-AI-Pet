"""
Pet Behavior Engine.
Processes confirmed food detections, updates pet state, enforces speech cooldowns,
and emits dialogue and animation events with playful, child-friendly personality.
Includes Autonomous Spontaneous Vocalization: the pet proactively speaks up
when it wants food, feels lonely & needs head pats, gets sleepy, or wants to play,
so the child never has to check or guess what the pet wants.
"""
from dataclasses import dataclass
from enum import Enum
import random
import time
from typing import Optional, Tuple

from ..audio.profiles import PetEmotion
from ..audio.renderer import SpeechIntent
from .state import PetState, PetMood, PetDesire
from .food_request import FoodRequestManager, FoodItem


class BehaviorOutcome(Enum):
    CORRECT = "CORRECT"
    WRONG = "WRONG"
    IGNORED_COOLDOWN = "IGNORED_COOLDOWN"
    IGNORED_NO_FOOD = "IGNORED_NO_FOOD"


@dataclass
class BehaviorEvent:
    outcome: BehaviorOutcome
    detected_food: str
    requested_food: str
    speech_text: Optional[str]
    is_correct: bool
    emotion: PetEmotion = PetEmotion.NEUTRAL
    intent: Optional[SpeechIntent] = None


class PetBehaviorEngine:
    def __init__(
        self,
        pet_state: PetState,
        food_manager: FoodRequestManager,
        cooldown_seconds: float = 3.0,
    ):
        self.state = pet_state
        self.food_manager = food_manager
        self.cooldown_seconds = cooldown_seconds
        self.last_response_time: float = 0.0

        # Autonomous vocalization timers (synchronized to epoch time.time())
        now = time.time()
        self._last_speech_time: float = now
        self._next_spontaneous_interval: float = random.uniform(18.0, 24.0)
        self._previous_mood: PetMood = pet_state.mood
        self._last_announced_food_id: Optional[str] = None
        self._pending_desire_announcement_time: Optional[float] = None
        self._hunger_reminder_count: int = 0
        self._last_vocalized_phrase: str = ""

        # Dialogues following the 5-15 words rule for young children (PRD Section 9 & 10)
        self.correct_phrases = [
            "Yay! That's exactly what I wanted! Thank you!",
            "Whoa! You found it! You are the best friend ever!",
            "Yummy yummy in my tummy! That was so delicious!",
            "Om-nom-nom! That was super tasty! High five!",
            "Yay, thank you! That was super duper yummy!",
        ]

        self.wrong_phrases = [
            "Hmm... that's not what I asked for. Let's try again!",
            "Oopsie-daisy! That looks yummy, but I really wanted {requested_name}.",
            "Tee-hee, almost! But my tummy is wishing for {requested_name}!",
            "Aww, good try! Could you find {requested_name} for me please?",
        ]

        # First hunger reminders (gentle, after ~18-22s)
        self.hunger_reminders_gentle = [
            "Hmm... my tummy is getting hungry. Can we find {requested_name}?",
            "Hey buddy! Could you help me find {requested_name}?",
            "Ooh, my tummy says snack time! Pretty please, can I have {requested_name}?",
            "I'm dreaming of some yummy {requested_name}! Is it ready?",
            "I'm feeling a little hungry! Can we have {requested_name} together?",
        ]

        # Escalated hunger reminders (when user hasn't given food yet after 20-25s)
        self.hunger_reminders_escalated = [
            "Rumble rumble! My tummy is still craving {requested_name}! Did you find it?",
            "I'm still wishing for {requested_name}! Pretty please, bestie?",
            "My tummy is waiting so patiently for {requested_name}!",
            "Hey bestie! Don't forget my {requested_name}, I'm super hungry!",
            "Rumble rumble! My tummy needs some yummy {requested_name} to recharge!",
        ]

        # Fallback list for compatibility
        self.hunger_reminders = self.hunger_reminders_gentle + self.hunger_reminders_escalated

        # Spontaneous food desire announcement right after eating or starting up
        self.food_desire_announcements = [
            "Ooh! Next, I would love some yummy {requested_name}!",
            "Hey bestie! My tummy is wishing for {requested_name} now!",
            "Mmm, I'm dreaming of {requested_name}! Can you find it for me?",
        ]

        self.startup_phrases = [
            "Yay, you're here! Hi bestie! I'm ready to play!",
            "Yippee! Hello friend! Let's find some yummy food!",
            "Hi sunshine! I'm so happy to see you today!",
        ]

        # When the user gives head pats / affection / strokes the pet
        self.pat_phrases = [
            "Tee-hee! That tickles! You give the best head pats!",
            "Purrrr, that feels so warm and cozy! More pats please!",
            "Aww, you're so sweet! I feel so happy and loved now!",
            "Yay! Soft head pats are my favorite thing in the whole world!",
            "Mmm, that's the spot! You're the best bestie ever!",
        ]

        # When the pet feels lonely and actively asks for head pats / usapan / cuddles
        self.lonely_affection_phrases = [
            "I'm feeling a little lonely... Can you give me some gentle head pats?",
            "Could you stroke my head? Warm pats make me feel so happy and safe!",
            "Bestie, are you there? I really miss your soft cuddles!",
            "Pet me please! My head is waiting for your gentle pats, tee-hee!",
            "A warm hug and head pats would make my day! Don't leave me alone, okay?",
            "Can I have some pats, please? I love when you stroke my forehead!",
            "Where did you go, buddy? Come pet me and play!",
        ]


        # Playful chatter when pet is happy and active
        self.play_phrases = [
            "I'm so happy today! What fun game should we play next?",
            "Yay, you're the best friend ever! Look at me bounce!",
            "Tee-hee, let's play together! Show me something fun!",
            "Having you here makes me so joyful! We make the best team!",
        ]

        self.sleepy_phrases = [
            "I'm getting sleepy... Maybe it's time for a little nap.",
            "Yaaawn... My eyes are heavy. Nap time feels nice.",
            "So sleepy... Could you stay close while I rest a bit?",
        ]

    def can_respond(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (now - self.last_response_time) >= self.cooldown_seconds

    def handle_confirmed_food(self, food_id_or_name: str) -> BehaviorEvent:
        """
        Processes a temporally confirmed food card detection.
        Returns a BehaviorEvent containing speech text, emotion, and outcome.
        """
        now = time.time()
        current_req = self.food_manager.current_request
        req_name = current_req.name if current_req else "food"
        req_id = current_req.id if current_req else "unknown"

        if not self.can_respond(now):
            return BehaviorEvent(
                outcome=BehaviorOutcome.IGNORED_COOLDOWN,
                detected_food=food_id_or_name,
                requested_food=req_id,
                speech_text=None,
                is_correct=False,
                emotion=PetEmotion.NEUTRAL,
                intent=None,
            )

        is_match = self.food_manager.matches(food_id_or_name)

        if is_match:
            self.last_response_time = now
            self._last_speech_time = now
            self._hunger_reminder_count = 0  # Reset reminder counter
            self.state.feed_success(hunger_delta=30.0, happiness_delta=20.0)
            speech = random.choice(self.correct_phrases)
            emotion = PetEmotion.HAPPY if "Whoa" not in speech else PetEmotion.EXCITED

            # Select a new random food request
            self.food_manager.select_random_request(exclude_current=True)
            intent = SpeechIntent(text=speech, emotion=emotion, priority=100)

            # Schedule spontaneous announcement of the new food desire after celebration (3.5s later)
            self._pending_desire_announcement_time = now + 4.0

            return BehaviorEvent(
                outcome=BehaviorOutcome.CORRECT,
                detected_food=food_id_or_name,
                requested_food=req_id,
                speech_text=speech,
                is_correct=True,
                emotion=emotion,
                intent=intent,
            )
        else:
            self.last_response_time = now
            self._last_speech_time = now
            self.state.feed_wrong(happiness_delta=3.0)
            template = random.choice(self.wrong_phrases)
            speech = template.format(requested_name=req_name.lower())
            emotion = PetEmotion.CONFUSED
            intent = SpeechIntent(text=speech, emotion=emotion, priority=80)

            return BehaviorEvent(
                outcome=BehaviorOutcome.WRONG,
                detected_food=food_id_or_name,
                requested_food=req_id,
                speech_text=speech,
                is_correct=False,
                emotion=emotion,
                intent=intent,
            )

    def _pick_non_repeating(self, phrases: list) -> str:
        candidates = [p for p in phrases if p != self._last_vocalized_phrase]
        chosen = random.choice(candidates if candidates else phrases)
        self._last_vocalized_phrase = chosen
        return chosen

    def check_autonomous_vocalization(self, current_time: Optional[float] = None) -> Optional[SpeechIntent]:
        """
        Evaluates whether the pet should spontaneously speak on its own without user interaction.
        Triggers when:
        1. Pending food desire announcement is due (e.g. after eating or starting up).
        2. Pet's mood changes spontaneously (e.g. becomes lonely or sleepy).
        3. Periodic spontaneous vocalization (every 18-25s): pet expresses its current
           strongest desire with paced, non-spam escalated reminders.
        """
        now = current_time if current_time is not None else time.time()

        # Do not interrupt if cooldown active
        if (now - self.last_response_time) < self.cooldown_seconds:
            return None

        current_req = self.food_manager.current_request
        req_name = current_req.name if current_req else "food"

        # 1. Check pending desire announcement (e.g. 3.8s after startup or eating)
        if (
            self._pending_desire_announcement_time is not None
            and now >= self._pending_desire_announcement_time
        ):
            self._pending_desire_announcement_time = None
            self._last_announced_food_id = current_req.id if current_req else None
            self.last_response_time = now
            self._last_speech_time = now
            self._next_spontaneous_interval = random.uniform(18.0, 24.0)
            self._hunger_reminder_count = 0

            template = self._pick_non_repeating(self.food_desire_announcements)
            text = template.format(requested_name=req_name.lower())
            return SpeechIntent(text=text, emotion=PetEmotion.HUNGRY, priority=75)

        # 2. Check mood transition (e.g. pet became lonely or sleepy passively)
        if self.state.mood != self._previous_mood:
            old_mood = self._previous_mood
            self._previous_mood = self.state.mood

            if self.state.mood == PetMood.LONELY and old_mood != PetMood.LONELY:
                self.last_response_time = now
                self._last_speech_time = now
                self._next_spontaneous_interval = random.uniform(18.0, 24.0)
                return self.get_lonely_intent()

            elif self.state.mood == PetMood.SLEEPY and old_mood != PetMood.SLEEPY:
                self.last_response_time = now
                self._last_speech_time = now
                self._next_spontaneous_interval = random.uniform(18.0, 24.0)
                return self.get_sleepy_intent()

        # 3. Periodic autonomous desire vocalization (every 18-25 seconds)
        time_since_speech = now - self._last_speech_time
        if time_since_speech >= self._next_spontaneous_interval:
            self.last_response_time = now
            self._last_speech_time = now
            self._next_spontaneous_interval = random.uniform(18.0, 25.0)

            desire = getattr(self.state, "current_desire", PetDesire.FOOD)

            if desire == PetDesire.FOOD:
                # Paced food reminders: gentle at first, then escalated if user hasn't fed yet
                if self._hunger_reminder_count == 0:
                    template = self._pick_non_repeating(self.hunger_reminders_gentle)
                else:
                    template = self._pick_non_repeating(self.hunger_reminders_escalated)

                self._hunger_reminder_count += 1
                text = template.format(requested_name=req_name.lower())
                return SpeechIntent(text=text, emotion=PetEmotion.HUNGRY, priority=70)

            elif desire == PetDesire.AFFECTION:
                phrase = self._pick_non_repeating(self.lonely_affection_phrases)
                return SpeechIntent(text=phrase, emotion=PetEmotion.LONELY, priority=75)

            elif desire == PetDesire.PLAY:
                phrase = self._pick_non_repeating(self.play_phrases)
                return SpeechIntent(text=phrase, emotion=PetEmotion.HAPPY, priority=65)

            elif desire == PetDesire.SLEEP:
                phrase = self._pick_non_repeating(self.sleepy_phrases)
                return SpeechIntent(text=phrase, emotion=PetEmotion.SLEEPY, priority=60)

        return None


    def schedule_initial_desire_announcement(self, delay: float = 3.5):
        """Schedules the pet to announce what food it wants shortly after startup greeting."""
        self._pending_desire_announcement_time = time.time() + delay

    def get_startup_phrase(self) -> str:
        return random.choice(self.startup_phrases)

    def get_startup_intent(self) -> SpeechIntent:
        phrase = self.get_startup_phrase()
        return SpeechIntent(text=phrase, emotion=PetEmotion.HAPPY, priority=90)

    def get_pat_phrase(self) -> str:
        return random.choice(self.pat_phrases)

    def get_pat_intent(self) -> SpeechIntent:
        now = time.time()
        self.last_response_time = now
        self._last_speech_time = now
        phrase = self.get_pat_phrase()
        return SpeechIntent(text=phrase, emotion=PetEmotion.HAPPY, priority=85)

    def get_hunger_reminder(self) -> Optional[str]:
        intent = self.get_hunger_reminder_intent()
        return intent.text if intent else None

    def get_hunger_reminder_intent(self) -> Optional[SpeechIntent]:
        now = time.time()
        if not self.can_respond(now):
            return None
        current_req = self.food_manager.current_request
        req_name = current_req.name if current_req else "something good"
        template = random.choice(self.hunger_reminders)
        self.last_response_time = now
        self._last_speech_time = now
        text = template.format(requested_name=req_name.lower())
        return SpeechIntent(text=text, emotion=PetEmotion.HUNGRY, priority=70)

    def get_sleepy_intent(self) -> SpeechIntent:
        phrase = random.choice(self.sleepy_phrases)
        return SpeechIntent(text=phrase, emotion=PetEmotion.SLEEPY, priority=60)

    def get_lonely_intent(self) -> SpeechIntent:
        phrase = random.choice(self.lonely_affection_phrases)
        return SpeechIntent(text=phrase, emotion=PetEmotion.LONELY, priority=75)
