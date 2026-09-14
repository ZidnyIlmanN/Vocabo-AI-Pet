"""
Unit tests for Pet State, Food Request Manager, and Behavior Engine.
"""
from pathlib import Path
import pytest
from app.pet.state import PetState, PetMood
from app.pet.food_request import FoodRequestManager, FoodItem
from app.pet.behavior import PetBehaviorEngine, BehaviorOutcome

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "food_catalog.json"


def test_pet_state_initial_values():
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=72.0, happiness=65.0, energy=80.0)
    assert state.mood == PetMood.HUNGRY
    assert state.hunger == 72.0
    assert state.happiness == 65.0
    assert state.energy == 80.0


def test_pet_state_setters_and_affection():
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=50.0, happiness=50.0, energy=50.0)
    state.hunger = 85.0
    state.happiness = 90.0
    state.energy = 40.0
    assert state.hunger == 85.0
    assert state.happiness == 90.0
    assert state.energy == 40.0

    # Test clamping
    state.happiness = 150.0
    assert state.happiness == 100.0
    state.hunger = -20.0
    assert state.hunger == 0.0

    # Test affection
    state.happiness = 50.0
    state.give_affection(15.0)
    assert state.happiness == 65.0


def test_pet_state_feed_success():
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=70.0, happiness=50.0)
    state.feed_success(hunger_delta=30.0, happiness_delta=20.0)
    assert state.hunger == 40.0
    assert state.happiness == 70.0
    assert state.mood == PetMood.HAPPY


def test_pet_state_feed_wrong():
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=70.0, happiness=50.0)
    state.feed_wrong(happiness_delta=5.0)
    assert state.hunger == 70.0  # Remains hungry
    assert state.happiness == 45.0
    assert state.mood == PetMood.HUNGRY


def test_food_request_manager_loading():
    mgr = FoodRequestManager(CATALOG_PATH)
    foods = mgr.get_all_foods()
    assert len(foods) >= 5

    # Check required classes exist
    food_ids = [f.id for f in foods]
    assert "rice_egg" in food_ids
    assert "fried_chicken" in food_ids
    assert "noodles" in food_ids
    assert "apple" in food_ids
    assert "milk" in food_ids


def test_food_matching_aliases():
    mgr = FoodRequestManager(CATALOG_PATH)
    mgr.select_request("rice_egg")

    assert mgr.matches("rice_egg") is True
    assert mgr.matches("Rice and Egg") is True
    assert mgr.matches("egg rice") is True
    assert mgr.matches("apple") is False


def test_behavior_engine_correct_and_wrong():
    mgr = FoodRequestManager(CATALOG_PATH)
    mgr.select_request("rice_egg")
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=70.0)
    engine = PetBehaviorEngine(state, mgr, cooldown_seconds=0.0)

    # 1. Test Wrong Food
    event_wrong = engine.handle_confirmed_food("apple")
    assert event_wrong.outcome == BehaviorOutcome.WRONG
    assert event_wrong.is_correct is False
    assert "apple" in event_wrong.detected_food
    assert state.mood == PetMood.HUNGRY

    # 2. Test Correct Food
    event_correct = engine.handle_confirmed_food("rice_egg")
    assert event_correct.outcome == BehaviorOutcome.CORRECT
    assert event_correct.is_correct is True
    assert state.mood == PetMood.HAPPY
    assert state.hunger < 70.0


def test_pet_desire_evaluation():
    from app.pet.state import PetDesire

    # Sleep when low energy
    sleepy_state = PetState(energy=15.0)
    assert sleepy_state.current_desire == PetDesire.SLEEP

    # Affection when lonely
    lonely_state = PetState(initial_mood=PetMood.LONELY, energy=80.0, hunger=30.0, happiness=40.0)
    assert lonely_state.current_desire == PetDesire.AFFECTION

    # Food when hungry
    hungry_state = PetState(initial_mood=PetMood.HUNGRY, energy=80.0, hunger=75.0, happiness=80.0)
    # Give affection right now so affection isn't stale
    hungry_state.give_affection(0.0)
    assert hungry_state.current_desire == PetDesire.FOOD

    # Play when full and happy
    happy_state = PetState(initial_mood=PetMood.HAPPY, energy=80.0, hunger=30.0, happiness=85.0)
    happy_state.give_affection(0.0)
    assert happy_state.current_desire == PetDesire.PLAY


def test_pet_lonely_affection_recovery():
    state = PetState(initial_mood=PetMood.LONELY, happiness=30.0)
    assert state.mood == PetMood.LONELY

    state.give_affection(happiness_boost=25.0)
    assert state.mood == PetMood.HAPPY
    assert state.happiness == 55.0



def test_autonomous_vocalization_lonely_and_affection():
    import time
    from app.audio.profiles import PetEmotion

    mgr = FoodRequestManager(CATALOG_PATH)
    state = PetState(initial_mood=PetMood.LONELY, hunger=30.0, happiness=30.0)
    engine = PetBehaviorEngine(state, mgr, cooldown_seconds=0.0)


    # Force interval to be expired
    now = time.time()
    engine._last_speech_time = now - 30.0
    engine.last_response_time = now - 10.0

    intent = engine.check_autonomous_vocalization(now)
    assert intent is not None
    assert intent.emotion == PetEmotion.LONELY
    assert any(pat_keyword in intent.text.lower() for pat_keyword in ["pat", "stroke", "cuddle", "lonely", "head", "buddy", "hug"])


def test_autonomous_vocalization_timing_and_cooldown():
    import time
    from app.audio.profiles import PetEmotion

    mgr = FoodRequestManager(CATALOG_PATH)
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=80.0)
    state.give_affection(0.0)  # Pet recently petted, so desire is FOOD
    engine = PetBehaviorEngine(state, mgr, cooldown_seconds=3.0)

    now = time.time()
    # 1. Cooldown active
    engine.last_response_time = now - 1.0
    engine._last_speech_time = now - 30.0
    assert engine.check_autonomous_vocalization(now) is None

    # 2. Cooldown passed and interval expired -> triggers hunger reminder
    engine.last_response_time = now - 5.0
    intent = engine.check_autonomous_vocalization(now)
    assert intent is not None
    assert intent.emotion == PetEmotion.HUNGRY


def test_food_desire_priority_and_escalated_reminders():
    import time
    from app.pet.state import PetDesire
    from app.audio.profiles import PetEmotion

    mgr = FoodRequestManager(CATALOG_PATH)
    mgr.select_request("rice_egg")

    # Pet with hunger >= 50 and time_since_affection > 25s
    state = PetState(initial_mood=PetMood.HUNGRY, hunger=70.0, happiness=50.0)
    state._time_since_affection = 30.0  # Even with high time since affection, hunger takes priority!
    assert state.current_desire == PetDesire.FOOD

    engine = PetBehaviorEngine(state, mgr, cooldown_seconds=0.0)
    now = time.time()
    engine._last_speech_time = now - 25.0
    engine.last_response_time = now - 10.0

    # First reminder should be from gentle reminders
    intent1 = engine.check_autonomous_vocalization(now)
    assert intent1 is not None
    assert intent1.emotion == PetEmotion.HUNGRY
    assert "rice" in intent1.text.lower() or "egg" in intent1.text.lower()
    assert engine._hunger_reminder_count == 1

    # Second reminder (user hasn't given food yet!)
    engine._last_speech_time = now - 25.0
    engine.last_response_time = now - 10.0
    intent2 = engine.check_autonomous_vocalization(now + 25.0)
    assert intent2 is not None
    assert intent2.emotion == PetEmotion.HUNGRY
    assert engine._hunger_reminder_count == 2
    # Verify non-duplicate phrase
    assert intent1.text != intent2.text


