"""
Independent 2D Animated Eye and Face Renderer.
Pure drawing machine that renders expressive, smooth 60 FPS vector eyes
from composited EyeFrame snapshots produced by EyeAnimationController.
PRD Section 18: Separation of state, animation logic, and rendering.
"""
import math
from typing import Optional, Tuple
import pygame

from .states import EyeState
from .events import EyeEvent
from .eye_config import EYE_CONFIG
from .eye_frame import EyeFrame
from .controller import EyeAnimationController


class EyeRenderer:
    """
    Renders digital pet facial features (eyes, blush, mouth) to any Pygame surface.
    Animation timing, physics, and state transitions are decoupled into EyeAnimationController.
    """

    def __init__(
        self,
        blink_min_interval: Optional[float] = None,
        blink_max_interval: Optional[float] = None,
        controller: Optional[EyeAnimationController] = None,
    ):
        # Configure controller
        if controller is not None:
            self.controller = controller
        else:
            cfg = dict(EYE_CONFIG)
            if blink_min_interval is not None or blink_max_interval is not None:
                blink_sub = dict(cfg["blink"])
                if blink_min_interval is not None:
                    blink_sub["min_interval"] = blink_min_interval
                if blink_max_interval is not None:
                    blink_sub["max_interval"] = blink_max_interval
                cfg["blink"] = blink_sub
            self.controller = EyeAnimationController(config=cfg)

        # Colors (Warm, modern, friendly child-oriented palette)
        self.eye_bg_color = (248, 249, 252)       # Soft warm white
        self.pupil_color = (35, 42, 58)           # Deep cute navy/charcoal
        self.highlight_color = (255, 255, 255)    # Pure sparkle
        self.blush_color = (255, 175, 189, 140)   # Soft cheerful blush
        self.mouth_color = (60, 64, 75)           # Cute dark mouth line
        self.happy_accent = (255, 215, 0)         # Golden sparkle

    # ──────────────────────────────────────────────────────────────────────────
    # Backward-Compatible Delegation Properties & Methods
    # ──────────────────────────────────────────────────────────────────────────
    @property
    def persistent_state(self) -> EyeState:
        return self.controller.persistent_state

    @persistent_state.setter
    def persistent_state(self, val: EyeState):
        self.controller.set_persistent_state(val)

    @property
    def active_event(self) -> Optional[EyeEvent]:
        return self.controller.active_event

    @property
    def is_blinking(self) -> bool:
        return self.controller.is_blinking

    @property
    def eyelid_open_fraction(self) -> float:
        return self.controller.eyelid_open_fraction

    @property
    def gaze_x(self) -> float:
        return self.controller.gaze_x

    @property
    def gaze_y(self) -> float:
        return self.controller.gaze_y

    @property
    def bounce_offset_y(self) -> float:
        return self.controller.bounce_offset_y

    @property
    def squash_stretch(self) -> float:
        return self.controller.squash_stretch

    def set_persistent_state(self, state: EyeState):
        """Sets current persistent emotional state."""
        self.controller.set_persistent_state(state)

    def trigger_event(self, event: EyeEvent) -> bool:
        """Triggers a temporary event animation if priority allows."""
        return self.controller.trigger_event(event)

    def get_effective_state(self) -> Tuple[EyeState, float]:
        """Returns the effective visual state and progress (0.0 to 1.0)."""
        return self.controller.get_effective_state()

    def update(self, dt: float) -> EyeFrame:
        """Updates animation logic via controller and returns updated EyeFrame."""
        return self.controller.update(dt)

    # ──────────────────────────────────────────────────────────────────────────
    # Rendering Pipeline
    # ──────────────────────────────────────────────────────────────────────────
    def render(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        frame: Optional[EyeFrame] = None,
    ):
        """
        Renders the pet face (eyes, blush, mouth) inside the specified rectangle.
        Consumes an EyeFrame snapshot (uses current controller frame if not provided).
        """
        if frame is None:
            frame = self.controller.get_current_frame()

        center_x = rect.centerx
        center_y = rect.centery + int(frame.bounce_y)

        eye_spacing = int(rect.width * 0.18)
        base_eye_width = int(rect.width * 0.13)
        base_eye_height = int(base_eye_width * 1.35 * frame.squash_stretch)

        left_eye_center = (center_x - eye_spacing, center_y - 20)
        right_eye_center = (center_x + eye_spacing, center_y - 20)

        # 1. Draw cute soft cheeks/blush
        blush_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        blush_radius = int(base_eye_width * 0.45)
        blush_y = center_y + int(base_eye_height * 0.55)
        pygame.draw.circle(
            blush_surface,
            self.blush_color,
            (left_eye_center[0] - int(base_eye_width * 0.3), blush_y),
            blush_radius,
        )
        pygame.draw.circle(
            blush_surface,
            self.blush_color,
            (right_eye_center[0] + int(base_eye_width * 0.3), blush_y),
            blush_radius,
        )
        surface.blit(blush_surface, rect.topleft)

        # 2. Draw left and right eye from EyeFrame
        self._render_eye(
            surface,
            left_eye_center,
            base_eye_width,
            base_eye_height,
            is_left=True,
            frame=frame,
        )
        self._render_eye(
            surface,
            right_eye_center,
            base_eye_width,
            base_eye_height,
            is_left=False,
            frame=frame,
        )

        # 3. Draw cute expressive mouth
        self._render_mouth(surface, (center_x, center_y + 65), frame.state)

    def _render_eye(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        width: int,
        height: int,
        is_left: bool,
        frame: EyeFrame,
    ):
        cx, cy = center
        state = frame.state

        # Effective openness for this specific eye
        open_fraction = (
            frame.effective_left_openness() if is_left else frame.effective_right_openness()
        )
        current_height = max(4, int(height * open_fraction))

        # 1. HAPPY state: Render cheerful inverted arc / crescent eyes (^ ^)
        if state == EyeState.HAPPY and open_fraction > 0.4:
            arc_rect = pygame.Rect(cx - width // 2, cy - height // 2, width, height)
            pygame.draw.arc(surface, self.pupil_color, arc_rect, 0.2, math.pi - 0.2, width=12)
            # Add small cute stars/sparkles around happy eyes
            sparkle_x = cx - width // 2 - 10 if is_left else cx + width // 2 + 10
            sparkle_y = cy - height // 3
            pygame.draw.circle(surface, self.happy_accent, (sparkle_x, sparkle_y), 4)
            return

        # 2. Fully closed / blinking line
        if open_fraction <= 0.15:
            pygame.draw.line(
                surface,
                self.pupil_color,
                (cx - width // 2, cy),
                (cx + width // 2, cy),
                width=8,
            )
            return

        # 3. Base eye socket (soft white pill/ellipse)
        eye_rect = pygame.Rect(cx - width // 2, cy - current_height // 2, width, current_height)
        pygame.draw.ellipse(surface, self.eye_bg_color, eye_rect)
        pygame.draw.ellipse(surface, (215, 222, 235), eye_rect, width=2)

        # 4. Pupil & Iris with frame pupil_scale
        base_radius = int(width * 0.42)
        pupil_radius = max(4, int(base_radius * frame.pupil_scale))

        # Gaze position from frame
        gaze_x = frame.left_x_offset if is_left else frame.right_x_offset
        gaze_y = frame.left_y_offset if is_left else frame.right_y_offset
        pupil_cx = cx + int(gaze_x)
        pupil_cy = cy + int(gaze_y)

        # Clamp pupil within eye boundary
        max_dx = width // 2 - pupil_radius - 2
        max_dy = max(2, current_height // 2 - pupil_radius - 2)
        pupil_cx = max(cx - max_dx, min(cx + max_dx, pupil_cx))
        pupil_cy = max(cy - max_dy, min(cy + max_dy, pupil_cy))

        # Draw pupil
        pygame.draw.circle(surface, self.pupil_color, (pupil_cx, pupil_cy), pupil_radius)

        # 5. Highlights (Sparkles for cuteness)
        if open_fraction > 0.5:
            # Big top highlight
            h1_x = pupil_cx - int(pupil_radius * 0.35)
            h1_y = pupil_cy - int(pupil_radius * 0.35)
            h1_r = max(2, int(pupil_radius * 0.34))
            pygame.draw.circle(surface, self.highlight_color, (h1_x, h1_y), h1_r)

            # Small bottom highlight
            h2_x = pupil_cx + int(pupil_radius * 0.35)
            h2_y = pupil_cy + int(pupil_radius * 0.35)
            h2_r = max(1, int(pupil_radius * 0.18))
            pygame.draw.circle(surface, self.highlight_color, (h2_x, h2_y), h2_r)

        # 6. Distinct Eyebrow / Eyelid shapes for emotions
        if state == EyeState.HUNGRY:
            # Drooped slightly sad/pleading upper eyelid
            lid_rect = pygame.Rect(
                cx - width // 2 - 2, cy - height // 2, width + 4, int(height * 0.35)
            )
            pygame.draw.ellipse(surface, (244, 246, 250), lid_rect)
        elif state == EyeState.SAD:
            # Inward slant
            slant_y_inner = cy - current_height // 2 + 10
            slant_y_outer = cy - current_height // 2 - 4
            p1 = (cx - width // 2, slant_y_outer if is_left else slant_y_inner)
            p2 = (cx + width // 2, slant_y_inner if is_left else slant_y_outer)
            pygame.draw.line(surface, self.pupil_color, p1, p2, width=4)
        elif state == EyeState.CONFUSED:
            # One eye cocked higher/tilted
            tilt = -8 if is_left else 8
            pygame.draw.line(
                surface,
                self.pupil_color,
                (cx - width // 2, cy - current_height // 2 - 10 + tilt),
                (cx + width // 2, cy - current_height // 2 - 10 - tilt),
                width=5,
            )
        elif state == EyeState.LONELY:
            # Soft pleading puppy-dog droop: slight inward-upward tilt brow & gentle upper lid droop
            brow_y_inner = cy - current_height // 2 - 2
            brow_y_outer = cy - current_height // 2 + 5
            p1 = (cx - width // 2, brow_y_outer if is_left else brow_y_inner)
            p2 = (cx + width // 2, brow_y_inner if is_left else brow_y_outer)
            pygame.draw.line(surface, self.pupil_color, p1, p2, width=3)
            lid_rect = pygame.Rect(
                cx - width // 2 - 1, cy - height // 2, width + 2, int(height * 0.28)
            )
            pygame.draw.ellipse(surface, (244, 246, 250), lid_rect)


    def _render_mouth(self, surface: pygame.Surface, center: Tuple[int, int], state: EyeState):
        cx, cy = center

        if state == EyeState.HAPPY:
            # Big cheerful open smile
            mouth_rect = pygame.Rect(cx - 24, cy - 14, 48, 28)
            pygame.draw.arc(surface, self.mouth_color, mouth_rect, math.pi, 2 * math.pi, width=4)
            # Soft inner smile tongue
            inner_rect = pygame.Rect(cx - 16, cy, 32, 16)
            pygame.draw.arc(surface, (255, 120, 130), inner_rect, math.pi, 2 * math.pi, width=3)
        elif state == EyeState.SURPRISED:
            # Cute small open 'o' mouth
            pygame.draw.ellipse(surface, self.mouth_color, (cx - 10, cy - 6, 20, 24), width=4)
        elif state in (EyeState.HUNGRY, EyeState.SAD, EyeState.LONELY):
            # Gentle soft pout/wavy mouth
            mouth_rect = pygame.Rect(cx - 18, cy + 2, 36, 18)
            pygame.draw.arc(surface, self.mouth_color, mouth_rect, 0.2, math.pi - 0.2, width=4)
        elif state == EyeState.CONFUSED:
            # Slightly sideways squiggly mouth
            points = [(cx - 16, cy + 4), (cx - 4, cy - 2), (cx + 8, cy + 6), (cx + 18, cy + 1)]
            pygame.draw.lines(surface, self.mouth_color, False, points, width=4)
        else:
            # Soft resting smile (Idle)
            mouth_rect = pygame.Rect(cx - 18, cy - 10, 36, 20)
            pygame.draw.arc(
                surface, self.mouth_color, mouth_rect, math.pi + 0.3, 2 * math.pi - 0.3, width=4
            )
