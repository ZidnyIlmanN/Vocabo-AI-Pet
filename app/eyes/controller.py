"""
Dynamic Eye Animation Controller.
Orchestrates layered animation systems and produces composited EyeFrame snapshots.
PRD Section 18 & 27: Architecture and layered compositing.
"""
import math
import random
import time
from typing import Optional, Tuple, Dict, Any

from .states import EyeState
from .events import EyeEvent, EVENT_PRIORITY, EVENT_DURATIONS
from .eye_config import EYE_CONFIG, get_profile
from .eye_frame import EyeFrame
from .animations import lerp, ease_in_out, ease_in_cubic, ease_out_cubic, calculate_blink_progress


class EyeAnimationController:
    """
    Core Animation Controller for the digital pet eyes.
    Manages 6 sub-systems:
      1. BlinkSystem (intervals, variations, double-blink, expression-aware)
      2. GazeSystem (target-based, dead zones, directional weights, anti-jitter)
      3. MicroMotionSystem (pupil flutter, asymmetry, micro-expressions)
      4. ExpressionTransitionSystem (smooth interpolation between states)
      5. EventAnimationSystem (anticipation -> reaction -> settle lifecycle)
      6. IdleBehaviorSystem (non-deterministic idle scheduler)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or EYE_CONFIG

        # ── 1. State Tracking & Expression Transition ─────────────────────
        self.persistent_state: EyeState = EyeState.IDLE
        self.prev_state: EyeState = EyeState.IDLE
        self.transition_timer: float = 0.0
        self.transition_duration: float = self.config["expression"]["transition_duration"]
        self.transition_progress: float = 1.0
        self.expression_openness: float = 1.0
        self.base_pupil_scale: float = 1.0

        # ── 2. Event Animation System ─────────────────────────────────────
        self.active_event: Optional[EyeEvent] = None
        self.event_timer: float = 0.0
        self.event_total_duration: float = 0.0
        self.event_phase: str = "none"       # "anticipation", "reaction", "settle", "none"
        self.event_intensity: float = 0.0
        self.anticipation_duration: float = self.config["event"]["anticipation_duration"]
        self.settle_duration: float = self.config["event"]["settle_duration"]

        # ── 3. Blink System ───────────────────────────────────────────────
        blink_cfg = self.config["blink"]
        self.blink_min_interval: float = blink_cfg["min_interval"]
        self.blink_max_interval: float = blink_cfg["max_interval"]
        self.normal_blink_duration: float = blink_cfg["normal_duration"]
        self.short_blink_duration: float = blink_cfg["short_duration"]
        self.long_blink_duration: float = blink_cfg["long_duration"]
        self.sleepy_blink_duration: float = blink_cfg["sleepy_duration"]
        self.double_blink_chance: float = blink_cfg["double_blink_chance"]
        self.short_blink_chance: float = blink_cfg["short_blink_chance"]
        self.long_blink_chance: float = blink_cfg["long_blink_chance"]
        self.double_blink_gap: float = blink_cfg["double_blink_gap"]
        self.post_surprise_cooldown: float = blink_cfg["post_surprise_cooldown"]

        self.is_blinking: bool = False
        self.blink_timer: float = 0.0
        self.current_blink_duration: float = self.normal_blink_duration
        self.time_until_next_blink: float = self._get_next_blink_interval()
        self.eyelid_open_fraction: float = 1.0
        self.is_double_blink_pending: bool = False
        self.post_surprise_timer: float = 0.0

        # ── 4. Gaze System ────────────────────────────────────────────────
        gaze_cfg = self.config["gaze"]
        self.max_gaze_x: float = gaze_cfg["max_x"]
        self.max_gaze_y: float = gaze_cfg["max_y"]
        self.gaze_transition_speed: float = gaze_cfg["transition_speed"]
        self.gaze_min_interval: float = gaze_cfg["min_interval"]
        self.gaze_max_interval: float = gaze_cfg["max_interval"]
        self.gaze_dead_zone: float = gaze_cfg["dead_zone"]
        self.gaze_min_movement: float = gaze_cfg["min_movement"]
        self.direction_weights: Dict[str, float] = gaze_cfg["direction_weights"]

        self.gaze_x: float = 0.0
        self.gaze_y: float = 0.0
        self.target_gaze_x: float = 0.0
        self.target_gaze_y: float = 0.0
        self.gaze_timer: float = 0.0
        self.gaze_interval: float = random.uniform(self.gaze_min_interval, self.gaze_max_interval)

        # ── 5. Micro Motion System ────────────────────────────────────────
        micro_cfg = self.config["micro_motion"]
        self.micro_motion_enabled: bool = micro_cfg["enabled"]
        self.micro_intensity: float = micro_cfg["intensity"]
        self.micro_min_interval: float = micro_cfg["min_interval"]
        self.micro_max_interval: float = micro_cfg["max_interval"]
        self.pupil_scale_range: float = micro_cfg["pupil_scale_range"]
        self.asymmetry_range: float = micro_cfg["asymmetry_range"]

        self.micro_timer: float = 0.0
        self.micro_interval: float = random.uniform(self.micro_min_interval, self.micro_max_interval)
        self.micro_time_acc: float = 0.0
        self.pupil_flutter: float = 0.0
        self.left_openness_mod: float = 0.0
        self.right_openness_mod: float = 0.0

        # ── 6. Idle Behavior System ───────────────────────────────────────
        idle_cfg = self.config["idle"]
        self.idle_min_quiet: float = idle_cfg["min_quiet_period"]
        self.idle_max_quiet: float = idle_cfg["max_quiet_period"]
        self.idle_micro_chance: float = idle_cfg["micro_expression_chance"]
        self.quiet_timer: float = 0.0
        self.quiet_duration: float = random.uniform(self.idle_min_quiet, self.idle_max_quiet)

        # ── 7. Body Motion (Bounce / Squash) ──────────────────────────────
        bounce_cfg = self.config["bounce"]
        self.bounce_amplitude: float = bounce_cfg["amplitude"]
        self.bounce_frequency: float = bounce_cfg["frequency"]
        self.squash_intensity: float = bounce_cfg["squash_intensity"]
        self.bounce_time: float = 0.0
        self.bounce_offset_y: float = 0.0
        self.squash_stretch: float = 1.0

        # Current composited frame
        self._current_frame: EyeFrame = EyeFrame()

    # ──────────────────────────────────────────────────────────────────────────
    # Helper & RNG Methods
    # ──────────────────────────────────────────────────────────────────────────
    def _get_next_blink_interval(self) -> float:
        return random.uniform(self.blink_min_interval, self.blink_max_interval)

    # ──────────────────────────────────────────────────────────────────────────
    # Public Control API (Preserving exact contracts)
    # ──────────────────────────────────────────────────────────────────────────
    def set_persistent_state(self, state: EyeState):
        """Sets current persistent emotional state, triggering a smooth transition."""
        if state != self.persistent_state:
            self.prev_state = self.persistent_state
            self.persistent_state = state
            self.transition_timer = 0.0
            self.transition_progress = 0.0

    def trigger_event(self, event: EyeEvent) -> bool:
        """
        Triggers a temporary event animation if it has higher or equal
        priority compared to any currently active event.
        """
        new_priority = EVENT_PRIORITY.get(event, 0)
        current_priority = EVENT_PRIORITY.get(self.active_event, 0) if self.active_event else -1

        if new_priority >= current_priority or self.active_event is None:
            self.active_event = event
            duration = EVENT_DURATIONS.get(event, 2.0)
            self.event_timer = duration
            self.event_total_duration = duration
            self.event_phase = "anticipation"
            self.event_intensity = 0.0

            # Reset blink if starting high-priority celebration or startup
            if event in (EyeEvent.CORRECT_FOOD, EyeEvent.STARTUP):
                self.is_blinking = False
                self.eyelid_open_fraction = 1.0

            # Post-surprise blink suppression
            if event == EyeEvent.FOOD_DETECTED:
                self.post_surprise_timer = self.post_surprise_cooldown
                self.is_blinking = False
                self.eyelid_open_fraction = 1.0

            return True
        return False

    def get_effective_state(self) -> Tuple[EyeState, float]:
        """
        Returns the effective visual state and progress (0.0 to 1.0)
        if an event is actively overriding persistent state.
        """
        if self.active_event is not None and self.event_total_duration > 0:
            progress = 1.0 - (self.event_timer / self.event_total_duration)
            if self.active_event == EyeEvent.CORRECT_FOOD:
                return EyeState.HAPPY, progress
            elif self.active_event == EyeEvent.WRONG_FOOD:
                return EyeState.CONFUSED, progress
            elif self.active_event == EyeEvent.FOOD_DETECTED:
                return EyeState.SURPRISED, progress
            elif self.active_event == EyeEvent.STARTUP:
                return EyeState.HAPPY, progress
            elif self.active_event == EyeEvent.ERROR:
                return EyeState.CONFUSED, progress

        return self.persistent_state, 1.0

    def get_current_frame(self) -> EyeFrame:
        """Returns the latest composited EyeFrame snapshot."""
        return self._current_frame

    # ──────────────────────────────────────────────────────────────────────────
    # Frame Update Pipeline
    # ──────────────────────────────────────────────────────────────────────────
    def update(self, dt: float) -> EyeFrame:
        """
        Updates all 6 animation sub-systems with elapsed delta time (seconds),
        composites all layers, and returns an EyeFrame snapshot.
        """
        # 1. Update Event Animation Lifecycle
        self._update_event_lifecycle(dt)

        effective_state, event_progress = self.get_effective_state()
        profile = get_profile(effective_state)

        # 2. Update Expression Transition
        self._update_expression_transition(dt, effective_state)

        # 3. Update Idle Behavior (if applicable)
        if effective_state == EyeState.IDLE and self.active_event is None:
            self._update_idle_behavior(dt)

        # 4. Update Blinking
        self._update_blinking(dt, effective_state, profile, event_progress)

        # 5. Update Gaze System
        self._update_gaze(dt, effective_state, profile)

        # 6. Update Micro Motion System
        self._update_micro_motion(dt, profile)

        # 7. Update Bounce & Squash-Stretch
        self._update_bounce(dt, effective_state, profile)

        # 8. Composite Final EyeFrame
        self._current_frame = EyeFrame(
            state=effective_state,
            prev_state=self.prev_state,
            expression_progress=self.transition_progress,
            eyelid_open=self.eyelid_open_fraction,
            left_openness_mod=self.left_openness_mod,
            right_openness_mod=self.right_openness_mod,
            left_x_offset=self.gaze_x,
            left_y_offset=self.gaze_y,
            right_x_offset=self.gaze_x,
            right_y_offset=self.gaze_y,
            pupil_scale=max(0.5, self.base_pupil_scale + self.pupil_flutter),
            expression_openness=self.expression_openness,
            bounce_y=self.bounce_offset_y,
            squash_stretch=self.squash_stretch,
            event_phase=self.event_phase,
            event_intensity=self.event_intensity,
            blink_timer_remaining=self.time_until_next_blink,
            gaze_target=(self.target_gaze_x, self.target_gaze_y),
            current_animation=effective_state.value,
        )

        return self._current_frame

    # ──────────────────────────────────────────────────────────────────────────
    # Sub-system Updates
    # ──────────────────────────────────────────────────────────────────────────
    def _update_event_lifecycle(self, dt: float):
        """Lifecycle: Anticipation (0.12s) -> Reaction -> Settle (0.22s)."""
        if self.active_event is None:
            self.event_phase = "none"
            self.event_intensity = 0.0
            return

        self.event_timer -= dt
        if self.event_timer <= 0:
            self.active_event = None
            self.event_timer = 0.0
            self.event_phase = "none"
            self.event_intensity = 0.0
            return

        elapsed = self.event_total_duration - self.event_timer
        if elapsed < self.anticipation_duration and self.anticipation_duration > 0:
            self.event_phase = "anticipation"
            self.event_intensity = ease_in_cubic(elapsed / self.anticipation_duration)
        elif self.event_timer < self.settle_duration and self.settle_duration > 0:
            self.event_phase = "settle"
            self.event_intensity = ease_out_cubic(self.event_timer / self.settle_duration)
        else:
            self.event_phase = "reaction"
            self.event_intensity = 1.0

    def _update_expression_transition(self, dt: float, target_state: EyeState):
        """Smoothly interpolates openness and pupil scale during expression shifts."""
        if self.transition_progress < 1.0:
            self.transition_timer += dt
            self.transition_progress = min(1.0, self.transition_timer / self.transition_duration)
            t = ease_in_out(self.transition_progress)

            prev_prof = get_profile(self.prev_state)
            curr_prof = get_profile(target_state)

            self.expression_openness = lerp(prev_prof["openness"], curr_prof["openness"], t)
            self.base_pupil_scale = lerp(prev_prof["pupil_scale"], curr_prof["pupil_scale"], t)
        else:
            prof = get_profile(target_state)
            self.expression_openness = prof["openness"]
            self.base_pupil_scale = prof["pupil_scale"]

    def _update_idle_behavior(self, dt: float):
        """Non-deterministic scheduler for resting idle state."""
        self.quiet_timer += dt
        if self.quiet_timer >= self.quiet_duration:
            self.quiet_timer = 0.0
            self.quiet_duration = random.uniform(self.idle_min_quiet, self.idle_max_quiet)

            # Chance to introduce a gentle micro-expression or trigger a natural gaze shift
            if random.random() < self.idle_micro_chance:
                # Slight asymmetric eyebrow/eye twitch
                asym = random.uniform(-self.asymmetry_range, self.asymmetry_range) * self.micro_intensity
                self.left_openness_mod = asym
                self.right_openness_mod = -asym

    def _update_blinking(self, dt: float, effective_state: EyeState, profile: dict, event_progress: float):
        """Manages eyelid open/close cycles, variations, double-blinks, and special events."""
        # Special startup wake-up sequence
        if self.active_event == EyeEvent.STARTUP and event_progress < 0.35:
            self.eyelid_open_fraction = ease_in_out(event_progress / 0.35)
            return

        # Decrement post-surprise cooldown
        if self.post_surprise_timer > 0:
            self.post_surprise_timer -= dt
            self.eyelid_open_fraction = 1.0
            return

        if self.is_blinking:
            self.blink_timer += dt
            self.eyelid_open_fraction = calculate_blink_progress(
                self.blink_timer, self.current_blink_duration
            )
            if self.blink_timer >= self.current_blink_duration:
                self.is_blinking = False
                self.eyelid_open_fraction = 1.0

                if self.is_double_blink_pending:
                    # Trigger immediate follow-up blink after short gap
                    self.is_double_blink_pending = False
                    self.time_until_next_blink = self.double_blink_gap
                else:
                    self.time_until_next_blink = self._get_next_blink_interval()
        else:
            self.time_until_next_blink -= dt
            if self.time_until_next_blink <= 0:
                self.is_blinking = True
                overflow_dt = max(0.0, -self.time_until_next_blink)
                self.blink_timer = overflow_dt

                # Determine blink duration and variation
                blink_speed_mult = profile.get("blink_speed", 1.0)
                if effective_state == EyeState.SLEEPY:
                    self.current_blink_duration = self.sleepy_blink_duration
                else:
                    r = random.random()
                    if r < self.double_blink_chance:
                        self.is_double_blink_pending = True
                        self.current_blink_duration = self.short_blink_duration * blink_speed_mult
                    elif r < self.double_blink_chance + self.short_blink_chance:
                        self.current_blink_duration = self.short_blink_duration * blink_speed_mult
                    elif r < self.double_blink_chance + self.short_blink_chance + self.long_blink_chance:
                        self.current_blink_duration = self.long_blink_duration * blink_speed_mult
                    else:
                        self.current_blink_duration = self.normal_blink_duration * blink_speed_mult

                self.eyelid_open_fraction = calculate_blink_progress(
                    self.blink_timer, self.current_blink_duration
                )


    def _select_new_gaze_target(self, effective_state: EyeState, profile: dict):
        """Selects a new target gaze with directional weights, expression bias, and dead zones."""
        gaze_mult = profile.get("gaze_range", 1.0)
        max_x = self.max_gaze_x * gaze_mult
        max_y = self.max_gaze_y * gaze_mult

        if effective_state == EyeState.LONELY:
            # Looks away towards edge
            cand_x = random.choice([-max_x, max_x]) * 0.95
            cand_y = random.uniform(2.0, max_y)
        elif effective_state == EyeState.HUNGRY:
            # Looks slightly down pleadingly
            cand_x = random.uniform(-max_x * 0.4, max_x * 0.4)
            cand_y = random.uniform(max_y * 0.5, max_y)
        elif effective_state == EyeState.CONFUSED:
            # Darting gaze left/right
            cand_x = random.choice([-max_x, max_x]) * 0.85
            cand_y = random.uniform(-max_y * 0.5, max_y * 0.5)
        elif effective_state in (EyeState.SURPRISED, EyeState.HAPPY):
            # Focus forward
            cand_x = 0.0
            cand_y = 0.0
        else:
            # Weighted random direction selection for IDLE/default
            weights = self.direction_weights
            dirs = list(weights.keys())
            probs = list(weights.values())
            chosen_dir = random.choices(dirs, weights=probs, k=1)[0]

            if chosen_dir == "center":
                cand_x, cand_y = 0.0, 0.0
            elif chosen_dir == "left":
                cand_x = -random.uniform(0.5, 1.0) * max_x
                cand_y = random.uniform(-0.3, 0.3) * max_y
            elif chosen_dir == "right":
                cand_x = random.uniform(0.5, 1.0) * max_x
                cand_y = random.uniform(-0.3, 0.3) * max_y
            elif chosen_dir == "up":
                cand_x = random.uniform(-0.3, 0.3) * max_x
                cand_y = -random.uniform(0.5, 1.0) * max_y
            elif chosen_dir == "down":
                cand_x = random.uniform(-0.3, 0.3) * max_x
                cand_y = random.uniform(0.5, 1.0) * max_y
            else:  # diagonal
                cand_x = random.choice([-1.0, 1.0]) * 0.7 * max_x
                cand_y = random.choice([-1.0, 1.0]) * 0.7 * max_y

        # Dead zone & anti-jitter check: ignore tiny movements
        dist = math.hypot(cand_x - self.gaze_x, cand_y - self.gaze_y)
        if dist >= self.gaze_dead_zone or dist < 0.01:
            self.target_gaze_x = cand_x
            self.target_gaze_y = cand_y

    def _update_gaze(self, dt: float, effective_state: EyeState, profile: dict):
        """Updates gaze targets periodically and smoothly interpolates towards them."""
        self.gaze_timer += dt
        if self.gaze_timer >= self.gaze_interval:
            self.gaze_timer = 0.0
            self.gaze_interval = random.uniform(self.gaze_min_interval, self.gaze_max_interval)
            self._select_new_gaze_target(effective_state, profile)

        # Smooth interpolation with expression-specific speed
        movement_speed = profile.get("movement_speed", 1.0)
        speed = self.gaze_transition_speed * movement_speed
        self.gaze_x = lerp(self.gaze_x, self.target_gaze_x, dt * speed)
        self.gaze_y = lerp(self.gaze_y, self.target_gaze_y, dt * speed)

    def _update_micro_motion(self, dt: float, profile: dict):
        """Subtle pupil flutter, asymmetry, and micro-expressions."""
        if not self.micro_motion_enabled:
            self.pupil_flutter = 0.0
            self.left_openness_mod = 0.0
            self.right_openness_mod = 0.0
            return

        self.micro_time_acc += dt

        # Continuous subtle pupil flutter (subtle breathing cycle)
        self.pupil_flutter = math.sin(self.micro_time_acc * 1.8) * self.pupil_scale_range * self.micro_intensity

        # Scheduled micro-expressions
        self.micro_timer += dt
        if self.micro_timer >= self.micro_interval:
            self.micro_timer = 0.0
            self.micro_interval = random.uniform(self.micro_min_interval, self.micro_max_interval)

            prob = profile.get("micro_expression_prob", 0.2)
            if random.random() < prob:
                asym = random.uniform(-self.asymmetry_range, self.asymmetry_range) * self.micro_intensity
                self.left_openness_mod = asym
                self.right_openness_mod = -asym

        # Smoothly decay any asymmetry back to 0
        self.left_openness_mod = lerp(self.left_openness_mod, 0.0, dt * 3.0)
        self.right_openness_mod = lerp(self.right_openness_mod, 0.0, dt * 3.0)

    def _update_bounce(self, dt: float, effective_state: EyeState, profile: dict):
        """Controlled cheerful bounce for HAPPY state or joyful events."""
        if profile.get("bounce_enabled", False):
            self.bounce_time += dt
            self.bounce_offset_y = -abs(math.sin(self.bounce_time * self.bounce_frequency)) * self.bounce_amplitude
            self.squash_stretch = 1.0 + math.sin(self.bounce_time * self.bounce_frequency) * self.squash_intensity
        else:
            self.bounce_offset_y = lerp(self.bounce_offset_y, 0.0, dt * 8.0)
            self.squash_stretch = lerp(self.squash_stretch, 1.0, dt * 8.0)
