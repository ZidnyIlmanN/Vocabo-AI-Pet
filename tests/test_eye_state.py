"""
Unit tests for Eye Animation State Machine, Controller, Priority Queue, and Compositing.
"""
import pytest
import pygame
from app.eyes.states import EyeState
from app.eyes.events import EyeEvent, EVENT_PRIORITY
from app.eyes.renderer import EyeRenderer
from app.eyes.controller import EyeAnimationController
from app.eyes.eye_frame import EyeFrame
from app.eyes.eye_config import EYE_CONFIG, get_profile
from app.eyes.animations import (
    calculate_blink_progress,
    lerp,
    ease_in_out,
    smoothstep,
    ease_out_cubic,
    ease_in_cubic,
)


def test_eye_event_priority_hierarchy():
    # Verify priority order as required by PRD Addendum Section 17
    assert EVENT_PRIORITY[EyeEvent.CORRECT_FOOD] > EVENT_PRIORITY[EyeEvent.WRONG_FOOD]
    assert EVENT_PRIORITY[EyeEvent.WRONG_FOOD] > EVENT_PRIORITY[EyeEvent.FOOD_DETECTED]
    assert EVENT_PRIORITY[EyeEvent.FOOD_DETECTED] > EVENT_PRIORITY[EyeEvent.ERROR]


def test_eye_renderer_overriding_and_recovery():
    renderer = EyeRenderer()
    renderer.set_persistent_state(EyeState.HUNGRY)

    effective_state, _ = renderer.get_effective_state()
    assert effective_state == EyeState.HUNGRY

    # Trigger temporary CORRECT_FOOD event
    triggered = renderer.trigger_event(EyeEvent.CORRECT_FOOD)
    assert triggered is True

    # While event is active, effective state should be HAPPY
    effective_state, _ = renderer.get_effective_state()
    assert effective_state == EyeState.HAPPY

    # Simulate event expiration
    renderer.update(dt=4.0)

    # Returns to persistent state
    effective_state, _ = renderer.get_effective_state()
    assert effective_state == EyeState.HUNGRY


def test_blink_progress_curve():
    # Start: 1.0 (Open)
    assert calculate_blink_progress(0.0, 0.2) == 1.0
    # Peak of blink (halfway): 0.0 (Closed)
    assert calculate_blink_progress(0.1, 0.2) == 0.0
    # End of blink: 1.0 (Open)
    assert calculate_blink_progress(0.2, 0.2) == 1.0


def test_easing_bounds():
    assert ease_in_out(0.0) == 0.0
    assert ease_in_out(1.0) == 1.0
    assert lerp(10.0, 20.0, 0.5) == 15.0


def test_new_easing_functions():
    # Smoothstep
    assert smoothstep(0.0, 1.0, 0.0) == 0.0
    assert smoothstep(0.0, 1.0, 1.0) == 1.0
    assert smoothstep(0.0, 1.0, 0.5) == 0.5
    assert smoothstep(5.0, 5.0, 5.0) == 0.0  # Zero range edge case

    # Cubic easings
    assert ease_out_cubic(0.0) == 0.0
    assert ease_out_cubic(1.0) == 1.0
    assert ease_in_cubic(0.0) == 0.0
    assert ease_in_cubic(1.0) == 1.0


def test_blink_variations_and_intervals():
    ctrl = EyeAnimationController()
    assert ctrl.blink_min_interval <= ctrl.time_until_next_blink <= ctrl.blink_max_interval

    # Trigger blink
    ctrl.time_until_next_blink = 0.01
    ctrl.update(0.02)
    assert ctrl.is_blinking is True
    assert ctrl.eyelid_open_fraction < 1.0

    # Finish blink
    ctrl.update(ctrl.current_blink_duration)
    assert ctrl.is_blinking is False
    assert ctrl.eyelid_open_fraction == 1.0


def test_gaze_dead_zone_and_bounds():
    ctrl = EyeAnimationController()
    profile = get_profile(EyeState.IDLE)
    ctrl._select_new_gaze_target(EyeState.IDLE, profile)

    # Candidate target should stay within max bounds
    assert abs(ctrl.target_gaze_x) <= ctrl.max_gaze_x * profile["gaze_range"] + 0.01
    assert abs(ctrl.target_gaze_y) <= ctrl.max_gaze_y * profile["gaze_range"] + 0.01

    # In HAPPY state, target gaze centers forward
    happy_profile = get_profile(EyeState.HAPPY)
    ctrl._select_new_gaze_target(EyeState.HAPPY, happy_profile)
    assert ctrl.target_gaze_x == 0.0
    assert ctrl.target_gaze_y == 0.0


def test_expression_smooth_transition():
    ctrl = EyeAnimationController()
    ctrl.set_persistent_state(EyeState.SLEEPY)

    # Initial frame
    frame0 = ctrl.update(0.0)
    assert frame0.state == EyeState.SLEEPY
    assert frame0.expression_progress == 0.0

    # Mid transition (at 0.14s into 0.28s)
    frame_mid = ctrl.update(0.14)
    assert 0.0 < frame_mid.expression_progress < 1.0
    assert 0.45 < frame_mid.expression_openness < 1.0

    # Completed transition
    frame_end = ctrl.update(0.20)
    assert frame_end.expression_progress == 1.0
    assert frame_end.expression_openness == pytest.approx(0.45, abs=0.01)


def test_event_anticipation_and_settle():
    ctrl = EyeAnimationController()
    ctrl.trigger_event(EyeEvent.FOOD_DETECTED)

    # Anticipation phase (< 0.12s)
    frame_anti = ctrl.update(0.05)
    assert frame_anti.event_phase == "anticipation"
    assert 0.0 < frame_anti.event_intensity < 1.0

    # Reaction phase (midpoint)
    frame_react = ctrl.update(0.3)
    assert frame_react.event_phase == "reaction"
    assert frame_react.event_intensity == 1.0

    # Settle phase (final 0.22s)
    remaining_to_settle = ctrl.event_timer - 0.1
    frame_settle = ctrl.update(remaining_to_settle)
    assert frame_settle.event_phase == "settle"
    assert 0.0 < frame_settle.event_intensity < 1.0

    # Finished
    frame_done = ctrl.update(0.5)
    assert frame_done.event_phase == "none"
    assert frame_done.event_intensity == 0.0


def test_micro_motion_bounds():
    ctrl = EyeAnimationController()
    ctrl.update(0.5)

    max_flutter = ctrl.pupil_scale_range * ctrl.micro_intensity + 0.001
    assert abs(ctrl.pupil_flutter) <= max_flutter

    # Test disabled micro motion
    cfg = dict(EYE_CONFIG)
    cfg["micro_motion"] = dict(cfg["micro_motion"])
    cfg["micro_motion"]["enabled"] = False
    ctrl_disabled = EyeAnimationController(config=cfg)
    ctrl_disabled.update(1.0)
    assert ctrl_disabled.pupil_flutter == 0.0
    assert ctrl_disabled.left_openness_mod == 0.0
    assert ctrl_disabled.right_openness_mod == 0.0


def test_eye_frame_compositing():
    frame = EyeFrame(
        eyelid_open=0.8,
        expression_openness=0.9,
        left_openness_mod=0.02,
        right_openness_mod=-0.02,
    )
    assert frame.effective_left_openness() == pytest.approx(0.8 * 0.9 + 0.02)
    assert frame.effective_right_openness() == pytest.approx(0.8 * 0.9 - 0.02)

    # Clamping test
    clamped_frame = EyeFrame(
        eyelid_open=0.0,
        expression_openness=0.5,
        left_openness_mod=-0.1,
    )
    assert clamped_frame.effective_left_openness() == 0.0


def test_renderer_backward_compatibility_and_render():
    renderer = EyeRenderer()
    renderer.set_persistent_state(EyeState.HAPPY)
    assert renderer.persistent_state == EyeState.HAPPY
    assert renderer.is_blinking is False
    assert renderer.eyelid_open_fraction == 1.0

    frame = renderer.update(0.016)
    assert isinstance(frame, EyeFrame)

    # Verify rendering to Pygame surface succeeds without error
    pygame.init()
    surface = pygame.Surface((300, 300))
    rect = pygame.Rect(0, 0, 300, 300)
    renderer.render(surface, rect)
    renderer.render(surface, rect, frame=frame)
