"""
Unit tests for Temporal Detection Stabilizer.
"""
import pytest
from app.vision.stabilizer import TemporalStabilizer


def test_stabilizer_requires_consecutive_frames():
    stab = TemporalStabilizer(required_consecutive_frames=5, confidence_threshold=0.70)

    # Feed 4 frames of rice_egg
    for i in range(4):
        res = stab.update(detected_id="rice_egg", confidence=0.85)
        assert res.is_confirmed is False
        assert res.consecutive_count == i + 1

    # 5th frame confirms detection
    res5 = stab.update(detected_id="rice_egg", confidence=0.85)
    assert res5.is_confirmed is True
    assert res5.food_id == "rice_egg"


def test_stabilizer_filters_low_confidence():
    stab = TemporalStabilizer(required_consecutive_frames=3, confidence_threshold=0.75)

    # Below threshold confidence (0.60 < 0.75)
    res1 = stab.update(detected_id="rice_egg", confidence=0.60)
    assert res1.is_confirmed is False
    assert res1.consecutive_count == 0


def test_stabilizer_resets_on_food_switch():
    stab = TemporalStabilizer(required_consecutive_frames=5, confidence_threshold=0.70)

    # 3 frames of noodles
    for _ in range(3):
        stab.update("noodles", 0.90)

    # Suddenly changes to fried_chicken
    res = stab.update("fried_chicken", 0.90)
    assert res.food_id == "fried_chicken"
    assert res.consecutive_count == 1
    assert res.is_confirmed is False


def test_stabilizer_resets_after_empty_frames():
    stab = TemporalStabilizer(required_consecutive_frames=5, confidence_threshold=0.70)

    # 3 frames of milk
    stab.update("milk", 0.90)
    stab.update("milk", 0.90)
    stab.update("milk", 0.90)

    # 3 empty frames
    for _ in range(3):
        res = stab.update(None, 0.0)

    assert res.consecutive_count == 0
    assert res.food_id == ""
    assert res.is_confirmed is False
