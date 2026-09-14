"""
Pygame Dashboard Layout — Scrapbook & Creative Notebook Paper Aesthetic.
Features lined graph paper canvas, polaroid photo frames, washi tape stickers,
folder tab telemetry cards, and vibrant sticker pills matching the reference design.
"""
from datetime import datetime
import math
from typing import List, Optional, Tuple
import cv2
import numpy as np
import pygame

from ..eyes.renderer import EyeRenderer
from ..pet.state import PetState, PetDesire, PetMood
from ..pet.food_request import FoodItem
from ..vision.stabilizer import StabilizedDetection


class Dashboard:
    def __init__(
        self,
        width: int = 1024,
        height: int = 768,
        title: str = "Interactive AI Pet Food Vision Prototype",
    ):
        self.width = width
        self.height = height
        self.title = title

        pygame.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        # Initialize fonts safely with clean fallbacks
        pygame.font.init()
        self.font_logo = pygame.font.SysFont("Impact", 22)
        self.font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_bold = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.font_speech = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.font_hand = pygame.font.SysFont("Segoe Script", 13)

        # Event log
        self.event_logs: List[str] = []
        self.max_logs = 5
        self.current_speech: str = ""
        self.speech_display_timer: float = 0.0

        # Scrapbook / Notebook Color Palette
        self.col_paper_bg = (250, 247, 242)        # Warm cream notebook paper
        self.col_paper_grid = (234, 230, 222)      # Subtle graph grid line
        self.col_paper_margin = (248, 205, 212)    # Faint notebook red margin
        self.col_ink_dark = (30, 34, 45)           # Sharp dark ink / borders
        self.col_ink_muted = (105, 115, 134)       # Soft grey text
        self.col_card_bg = (255, 255, 255)         # Crisp polaroid white
        self.col_card_shadow = (30, 34, 45)        # Hard neo-brutalist paper shadow

        # Vibrant Accent Sticker Colors (from reference image)
        self.col_yellow = (252, 211, 77)           # Mustard yellow
        self.col_green = (52, 211, 153)            # Mint / emerald
        self.col_pink = (244, 63, 94)              # Candy pink / rose
        self.col_blue = (37, 99, 235)              # Royal / cobalt blue
        self.col_purple = (168, 85, 247)           # Lavender
        self.col_orange = (249, 115, 22)           # Tangerine

        # Layout Rectangles (Grid-aligned)
        self.rect_header = pygame.Rect(16, 10, self.width - 32, 36)
        top_h = 320
        self.rect_pet = pygame.Rect(16, 54, self.width - 32, top_h)

        bottom_y = 54 + top_h + 16
        bottom_h = self.height - bottom_y - 36
        left_w = int((self.width - 44) * 0.48)
        right_w = self.width - left_w - 44

        self.rect_camera = pygame.Rect(16, bottom_y, left_w, bottom_h)
        self.rect_status = pygame.Rect(16 + left_w + 12, bottom_y, right_w, bottom_h)
        self.rect_footer = pygame.Rect(16, self.height - 28, self.width - 32, 22)

        # Pre-cache washi tape surfaces
        self.tape_surf_left = self._create_tape_surface(width=58, height=18, angle=-18)
        self.tape_surf_right = self._create_tape_surface(width=58, height=18, angle=18)

    # ──────────────────────────────────────────────────────────────────────────
    # Scrapbook Aesthetic Helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _create_tape_surface(self, width: int = 58, height: int = 18, angle: float = 15) -> pygame.Surface:
        """Creates a semi-transparent rotated washi tape strip."""
        surf = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA)
        tape_rect = pygame.Rect(10, 10, width, height)

        # Translucent frosted paper tape
        pygame.draw.rect(surf, (255, 255, 255, 175), tape_rect, border_radius=2)
        pygame.draw.rect(surf, (220, 215, 200, 140), tape_rect, width=1, border_radius=2)

        # Subtle tape fiber stripes
        for x in range(tape_rect.left + 8, tape_rect.right - 6, 8):
            pygame.draw.line(surf, (210, 205, 190, 80), (x, tape_rect.top), (x, tape_rect.bottom), 1)

        return pygame.transform.rotate(surf, angle)

    def _draw_paper_background(self):
        """Renders cream notebook paper canvas with subtle 24px grid lines."""
        self.screen.fill(self.col_paper_bg)

        # Draw subtle graph paper grid
        grid_step = 24
        for x in range(0, self.width, grid_step):
            pygame.draw.line(self.screen, self.col_paper_grid, (x, 0), (x, self.height), 1)
        for y in range(0, self.height, grid_step):
            pygame.draw.line(self.screen, self.col_paper_grid, (0, y), (self.width, y), 1)

        # Faint left margin line (notebook spine line)
        pygame.draw.line(self.screen, self.col_paper_margin, (32, 0), (32, self.height), 2)

    def _draw_card_frame(
        self,
        rect: pygame.Rect,
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        border_radius: int = 12,
        tape_corners: bool = True,
        shadow_offset: int = 4,
    ):
        """Draws a scrapbook / polaroid card with hard offset shadow and taped corners."""
        # 1. Hard offset drop shadow (neo-brutalist / paper cutout)
        shadow_rect = pygame.Rect(
            rect.x + shadow_offset, rect.y + shadow_offset, rect.width, rect.height
        )
        pygame.draw.rect(self.screen, self.col_card_shadow, shadow_rect, border_radius=border_radius)

        # 2. Main card body
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=border_radius)
        pygame.draw.rect(self.screen, self.col_ink_dark, rect, width=2, border_radius=border_radius)

        # 3. Translucent washi tape strips across top corners
        if tape_corners:
            self.screen.blit(self.tape_surf_left, (rect.left - 10, rect.top - 10))
            self.screen.blit(self.tape_surf_right, (rect.right - 56, rect.top - 10))

    def _draw_pill_badge(
        self,
        text: str,
        x: int,
        y: int,
        bg_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int] = (30, 34, 45),
        font: Optional[pygame.font.Font] = None,
        padding_x: int = 10,
        height: int = 24,
    ) -> int:
        """Draws a playful rounded pill badge with 1.5px dark border."""
        use_font = font or self.font_small
        t_surf = use_font.render(text, True, text_color)
        pill_w = t_surf.get_width() + padding_x * 2
        pill_rect = pygame.Rect(x, y, pill_w, height)

        pygame.draw.rect(self.screen, bg_color, pill_rect, border_radius=height // 2)
        pygame.draw.rect(self.screen, self.col_ink_dark, pill_rect, width=2, border_radius=height // 2)
        self.screen.blit(t_surf, (x + padding_x, y + (height - t_surf.get_height()) // 2))

        return pill_w

    # ──────────────────────────────────────────────────────────────────────────
    # Public Event / Timing API
    # ──────────────────────────────────────────────────────────────────────────
    def log_event(self, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        entry = f"{now_str} {message}"
        self.event_logs.append(entry)
        if len(self.event_logs) > self.max_logs:
            self.event_logs.pop(0)

    def set_speech(self, text: str, duration: float = 5.0):
        self.current_speech = text
        self.speech_display_timer = duration

    def update_timers(self, dt: float):
        if self.speech_display_timer > 0:
            self.speech_display_timer -= dt
            if self.speech_display_timer <= 0:
                self.current_speech = ""

    # ──────────────────────────────────────────────────────────────────────────
    # Main Render Pipeline
    # ──────────────────────────────────────────────────────────────────────────
    def render(
        self,
        eye_renderer: EyeRenderer,
        pet_state: PetState,
        current_request: Optional[FoodItem],
        camera_frame_bgr: Optional[np.ndarray],
        stabilized_detection: StabilizedDetection,
        fps: float,
    ):
        # 1. Base Graph Paper Canvas
        self._draw_paper_background()

        # 2. Header Bar with Tabs and Avatar Badges (Reference Style)
        self._render_header_bar()

        # 3. Virtual Pet Polaroid Stage
        self._render_pet_stage(eye_renderer)

        # 4. Camera HUD Polaroid Card
        self._render_camera_hud(camera_frame_bgr, stabilized_detection, current_request)

        # 5. Folder Tab Telemetry & Desire Card
        self._render_status_card(pet_state, current_request, stabilized_detection)

        # 6. Pinned Paper Footer Ribbon
        self._render_footer(fps)

        pygame.display.flip()

    # ──────────────────────────────────────────────────────────────────────────
    # Sub-component Rendering
    # ──────────────────────────────────────────────────────────────────────────
    def _render_header_bar(self):
        """Top navigation bar with pill buttons and playful colorful circles."""
        bar_y = self.rect_header.y

        # Left Nav Tabs (Matching reference design top-left)
        x = self.rect_header.x + 8
        x += self._draw_pill_badge("PET STAGE", x, bar_y, self.col_yellow, height=28) + 8
        x += self._draw_pill_badge("VISION HUD", x, bar_y, (255, 255, 255), height=28) + 8
        x += self._draw_pill_badge("TELEMETRY", x, bar_y, (255, 255, 255), height=28) + 8

        # Center handwritten annotation doodle
        center_x = self.width // 2
        doodle_surf = self.font_bold.render("PELY COMPANION", True, self.col_ink_dark)
        tag_rect = pygame.Rect(center_x - doodle_surf.get_width() // 2 - 12, bar_y, doodle_surf.get_width() + 24, 28)
        pygame.draw.rect(self.screen, self.col_card_bg, tag_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.col_orange, tag_rect, width=2, border_radius=6)
        self.screen.blit(doodle_surf, (center_x - doodle_surf.get_width() // 2, bar_y + 4))

        # Right-side colorful badge circle avatars (Matching reference top-right)
        circle_x = self.rect_header.right - 100
        avatar_colors = [self.col_yellow, self.col_green, self.col_pink, self.col_blue]
        for col in avatar_colors:
            pygame.draw.circle(self.screen, col, (circle_x, bar_y + 14), 10)
            pygame.draw.circle(self.screen, self.col_ink_dark, (circle_x, bar_y + 14), 10, width=2)
            circle_x += 24

    def _render_pet_stage(self, eye_renderer: EyeRenderer):
        """Polaroid canvas for the 60 FPS animated pet face with speech bubble."""
        self._draw_card_frame(self.rect_pet, bg_color=(255, 255, 255), border_radius=14, tape_corners=True)

        # Stage Header Sticker Tag
        self._draw_pill_badge("VIRTUAL STAGE", self.rect_pet.x + 22, self.rect_pet.y + 16, self.col_yellow)

        # Subtitle tag
        sub_surf = self.font_small.render("Interactive Touch & Vision Enabled", True, self.col_ink_muted)
        self.screen.blit(sub_surf, (self.rect_pet.x + 145, self.rect_pet.y + 20))

        # Pet Face Viewport (Nicely centered)
        eye_viewport = pygame.Rect(
            self.rect_pet.x + 20,
            self.rect_pet.y + 30,
            self.rect_pet.width - 40,
            self.rect_pet.height - 85,
        )
        eye_renderer.render(self.screen, eye_viewport)

        # Comic-style Speech Bubble with Hard Drop Shadow and Pointer Tail
        if self.current_speech:
            self._render_speech_bubble(self.current_speech)

    def _render_speech_bubble(self, text: str):
        """Scrapbook speech bubble with thick ink border and pointer tail."""
        text_surf = self.font_speech.render(f'"{text}"', True, self.col_ink_dark)
        bubble_w = text_surf.get_width() + 36
        bubble_h = text_surf.get_height() + 18
        bubble_x = self.rect_pet.centerx - bubble_w // 2
        bubble_y = self.rect_pet.bottom - bubble_h - 14

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)

        # Hard drop shadow
        pygame.draw.rect(
            self.screen, self.col_ink_dark, (bubble_x + 3, bubble_y + 3, bubble_w, bubble_h), border_radius=12
        )

        # Tail shadow
        tail_tip_x = self.rect_pet.centerx
        tail_shadow_pts = [
            (tail_tip_x - 12 + 3, bubble_y + 3),
            (tail_tip_x + 3, bubble_y - 10 + 3),
            (tail_tip_x + 12 + 3, bubble_y + 3),
        ]
        pygame.draw.polygon(self.screen, self.col_ink_dark, tail_shadow_pts)

        # Bubble body
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.col_ink_dark, bubble_rect, width=2, border_radius=12)

        # Pointer tail body
        tail_pts = [
            (tail_tip_x - 12, bubble_y + 1),
            (tail_tip_x, bubble_y - 10),
            (tail_tip_x + 12, bubble_y + 1),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), tail_pts)
        pygame.draw.lines(self.screen, self.col_ink_dark, False, [(tail_tip_x - 12, bubble_y + 1), (tail_tip_x, bubble_y - 10), (tail_tip_x + 12, bubble_y + 1)], width=2)

        self.screen.blit(text_surf, (bubble_x + 18, bubble_y + 9))

    def _render_camera_hud(
        self,
        frame_bgr: Optional[np.ndarray],
        detection: StabilizedDetection,
        current_req: Optional[FoodItem],
    ):
        """Camera feed styled like a Polaroid photo print pinned with tape."""
        self._draw_card_frame(self.rect_camera, bg_color=(255, 255, 255), border_radius=12, tape_corners=True)

        # Card Title Sticker
        self._draw_pill_badge("CAMERA FEED", self.rect_camera.x + 18, self.rect_camera.y + 14, self.col_green)


        # Inset Viewport for camera frame (Polaroid photo aperture)
        cam_view = pygame.Rect(
            self.rect_camera.x + 16,
            self.rect_camera.y + 44,
            self.rect_camera.width - 32,
            int(self.rect_camera.height * 0.62),
        )

        if frame_bgr is not None:
            display_bgr = frame_bgr.copy()
            if detection.box is not None:
                x1, y1, x2, y2 = detection.box
                is_correct = current_req and detection.food_id == current_req.id
                box_color = (34, 197, 94) if is_correct else (244, 63, 94)
                cv2.rectangle(display_bgr, (x1, y1), (x2, y2), box_color, 3)
                label = f"{detection.food_id} ({int(detection.confidence * 100)}%)"
                cv2.putText(
                    display_bgr,
                    label,
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    box_color,
                    2,
                )

            frame_rgb = cv2.cvtColor(display_bgr, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (cam_view.width, cam_view.height))
            surf = pygame.surfarray.make_surface(np.rot90(frame_resized))
            surf = pygame.transform.flip(surf, True, False)
            self.screen.blit(surf, cam_view.topleft)
        else:
            pygame.draw.rect(self.screen, (240, 238, 230), cam_view, border_radius=6)
            t = self.font_body.render("Camera Offline", True, self.col_ink_muted)
            self.screen.blit(t, (cam_view.centerx - 45, cam_view.centery - 10))

        # Thin inner frame border
        pygame.draw.rect(self.screen, self.col_ink_dark, cam_view, width=2, border_radius=6)

        # Polaroid Bottom Margin Caption Area
        meta_y = cam_view.bottom + 10
        if detection.food_id:
            status_txt = f"Detected: {detection.food_id.title()}"
            conf_txt = f"Confidence: {int(detection.confidence * 100)}%"
            is_match = current_req and detection.food_id == current_req.id
            tag_color = self.col_green if is_match else self.col_pink
            result_txt = "MATCHED" if is_match else "WRONG CARD"
        else:
            status_txt = "Card: None"
            conf_txt = "Looking for Food Card..."
            tag_color = self.col_ink_muted
            result_txt = "Waiting..."


        self.screen.blit(self.font_bold.render(status_txt, True, self.col_ink_dark), (self.rect_camera.x + 18, meta_y))
        self.screen.blit(self.font_small.render(conf_txt, True, self.col_ink_muted), (self.rect_camera.x + 18, meta_y + 20))

        # Right-aligned result sticker
        res_bg = self.col_yellow if not detection.food_id else (tag_color if is_match else self.col_pink)
        self._draw_pill_badge(result_txt, self.rect_camera.right - 120, meta_y + 4, res_bg)

    def _render_status_card(
        self,
        state: PetState,
        current_req: Optional[FoodItem],
        detection: StabilizedDetection,
    ):
        """Telemetry card styled as an archival folder tab with sticker badges."""
        rect = self.rect_status

        # 1. Folder Tab on top (Matching "Tandem / Project 01" folder tab style)
        tab_w = 190
        tab_h = 24
        tab_rect = pygame.Rect(rect.x + 14, rect.y - tab_h + 2, tab_w, tab_h)

        # Tab shadow and body
        pygame.draw.rect(self.screen, self.col_card_shadow, (tab_rect.x + 3, tab_rect.y + 3, tab_w, tab_h), border_radius=6)
        pygame.draw.rect(self.screen, self.col_blue, tab_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.col_ink_dark, tab_rect, width=2, border_radius=6)
        tab_text = self.font_small.render("PET TELEMETRY", True, (255, 255, 255))
        self.screen.blit(tab_text, (tab_rect.x + 22, tab_rect.y + 4))

        # 2. Main card body
        self._draw_card_frame(rect, bg_color=(255, 255, 255), border_radius=12, tape_corners=True)

        start_x = rect.x + 18
        cur_y = rect.y + 16

        # Mood badge
        mood_val = state.mood.value
        mood_col = self.col_yellow if mood_val == "HAPPY" else (self.col_pink if mood_val == "HUNGRY" else self.col_purple)
        self.screen.blit(self.font_bold.render("MOOD:", True, self.col_ink_dark), (start_x, cur_y + 4))
        self._draw_pill_badge(f"{mood_val}", start_x + 60, cur_y, mood_col)

        # Timestamp note
        now_time = datetime.now().strftime("%I:%M %p")
        time_surf = self.font_small.render(now_time, True, self.col_ink_muted)
        self.screen.blit(time_surf, (rect.right - 80, cur_y + 4))
        cur_y += 32

        # 3. Colorful Sticker Progress Bars
        cur_y = self._draw_scrapbook_bar(start_x, cur_y, "Hunger", state.hunger, self.col_pink)
        cur_y = self._draw_scrapbook_bar(start_x, cur_y, "Happiness", state.happiness, self.col_green)
        cur_y = self._draw_scrapbook_bar(start_x, cur_y, "Energy", state.energy, self.col_blue)

        # 4. CURRENT DESIRE STICKER CARD (Pinned Note)
        cur_y += 4
        desire = getattr(state, "current_desire", PetDesire.FOOD)

        desire_box = pygame.Rect(start_x, cur_y, rect.width - 36, 52)
        if desire == PetDesire.AFFECTION:
            d_bg = (255, 228, 230)
            d_text = "Head Pats & Cuddles"
            d_sub = "Pet me by clicking face on screen!"
        elif desire == PetDesire.SLEEP:
            d_bg = (237, 233, 254)
            d_text = "Nap & Rest Time"
            d_sub = "Drowsy, recharging energy..."
        elif desire == PetDesire.PLAY:
            d_bg = (209, 250, 229)
            d_text = "Play Games & Fun!"
            d_sub = "Full of energy, ready to explore!"
        elif current_req:
            d_bg = (254, 243, 199)
            d_text = f"{current_req.name}"
            d_sub = "Awaiting food card in front of camera"
        else:
            d_bg = (245, 245, 245)
            d_text = "Nothing Right Now"
            d_sub = "Relaxing comfortably"


        # Desire note shadow & body
        pygame.draw.rect(self.screen, self.col_card_shadow, (desire_box.x + 2, desire_box.y + 2, desire_box.width, desire_box.height), border_radius=8)
        pygame.draw.rect(self.screen, d_bg, desire_box, border_radius=8)
        pygame.draw.rect(self.screen, self.col_ink_dark, desire_box, width=2, border_radius=8)

        # Tiny taped corner on the desire note
        self.screen.blit(self.tape_surf_right, (desire_box.right - 35, desire_box.top - 8))

        label_title = self.font_small.render("CURRENT DESIRE:", True, self.col_ink_muted)
        self.screen.blit(label_title, (desire_box.x + 10, desire_box.y + 6))
        main_d_surf = self.font_bold.render(d_text, True, self.col_ink_dark)
        self.screen.blit(main_d_surf, (desire_box.x + 10, desire_box.y + 20))
        sub_d_surf = self.font_small.render(d_sub, True, self.col_ink_muted)
        self.screen.blit(sub_d_surf, (desire_box.x + 10, desire_box.y + 36))

        cur_y += 62

        # 5. Recent Event Log (Mini Lined Notepad)
        self.screen.blit(self.font_small.render("RECENT ACTIVITY:", True, self.col_ink_muted), (start_x, cur_y))
        cur_y += 16
        for entry in self.event_logs[-3:]:
            log_surf = self.font_small.render(f"• {entry}", True, self.col_ink_dark)
            self.screen.blit(log_surf, (start_x, cur_y))
            cur_y += 15

    def _draw_scrapbook_bar(
        self,
        x: int,
        y: int,
        label: str,
        value: float,
        color: Tuple[int, int, int],
    ) -> int:
        """Draws a rounded neo-brutalist progress bar with dark border."""
        label_surf = self.font_small.render(f"{label}", True, self.col_ink_dark)
        pct_surf = self.font_small.render(f"{int(value)}%", True, self.col_ink_muted)
        self.screen.blit(label_surf, (x, y))
        self.screen.blit(pct_surf, (self.rect_status.right - 55, y))

        bar_w = self.rect_status.width - 36
        bar_h = 10
        bar_rect = pygame.Rect(x, y + 15, bar_w, bar_h)
        fill_w = int(bar_w * (max(0.0, min(100.0, value)) / 100.0))
        fill_rect = pygame.Rect(x, y + 15, fill_w, bar_h)

        # Bar track
        pygame.draw.rect(self.screen, (240, 238, 232), bar_rect, border_radius=5)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, fill_rect, border_radius=5)
        # Bar border
        pygame.draw.rect(self.screen, self.col_ink_dark, bar_rect, width=1, border_radius=5)

        return y + 30

    def _render_footer(self, fps: float):
        """Paper ribbon strip with keyboard and mouse hotkey hints."""
        rect = self.rect_footer
        self._draw_card_frame(rect, bg_color=(255, 255, 255), border_radius=6, tape_corners=False, shadow_offset=2)

        help_text = "Controls: Click Pet or [P] Pet  |  [1-5] Food Cards  |  [R] Next Food  |  [Q/Esc] Exit"
        fps_text = f"{int(fps)} FPS"

        h_surf = self.font_small.render(help_text, True, self.col_ink_dark)
        f_surf = self.font_small.render(fps_text, True, self.col_green)

        self.screen.blit(h_surf, (rect.x + 12, rect.y + 4))
        self.screen.blit(f_surf, (rect.right - 55, rect.y + 4))

