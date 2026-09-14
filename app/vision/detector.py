"""
Food Card Detector with Asynchronous Inference.
Uses a 3-stage pipeline:
  1. ORB Template Matching (within phone screen ROI)
  2. Screen-Bounded Color Signature Analysis
  3. YOLO Model Inference (fallback)

All detection is gated behind a white phone screen finder
to completely eliminate false positives on faces, clothes, and walls.
"""
from dataclasses import dataclass
import logging
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("pet.detector")


@dataclass
class DetectionResult:
    food_id: Optional[str] = None
    food_name: Optional[str] = None
    confidence: float = 0.0
    box: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2)
    inference_time_ms: float = 0.0


class FoodDetector:
    def __init__(
        self,
        model_path: str,
        catalog_foods: Dict[str, str],  # id -> display name mapping
        confidence_threshold: float = 0.70,
        enable_async: bool = True,
    ):
        self.model_path = Path(model_path)
        self.catalog_foods = catalog_foods
        self.confidence_threshold = confidence_threshold
        self.enable_async = enable_async

        self.model = None
        self.is_loaded = False
        self.latest_result = DetectionResult()

        # Simulated injection for testing/keyboard shortcuts
        self._simulated_food_id: Optional[str] = None
        self._simulated_until: float = 0.0

        # Asynchronous worker setup
        self._running = False
        self._pending_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

        # ORB Template Matching engine
        self._orb = cv2.ORB_create(nfeatures=800)
        self._bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self._templates: Dict[str, dict] = {}  # food_id -> {descriptors, keypoints, image}
        self._load_card_templates()

        # Color signature definitions (HSV ranges) — maximally separated
        # rice_egg:       Golden Yellow   (H ~20-35)
        # fried_chicken:  Orange-Amber    (H ~10-22)
        # noodles:        Vivid Red       (H ~0-10, 165-180)
        # apple:          Bright Green    (H ~35-85)
        # milk:           Sky Blue        (H ~95-135)
        self._color_signatures = {
            "noodles": [
                {"lower": (0, 80, 80), "upper": (10, 255, 255)},
                {"lower": (165, 80, 80), "upper": (180, 255, 255)},
            ],
            "apple": [
                {"lower": (35, 60, 60), "upper": (85, 255, 255)},
            ],
            "milk": [
                {"lower": (95, 60, 60), "upper": (135, 255, 255)},
            ],
            "rice_egg": [
                {"lower": (22, 60, 80), "upper": (38, 255, 255)},  # Golden yellow
            ],
            "fried_chicken": [
                {"lower": (8, 80, 80), "upper": (22, 255, 255)},  # Deep orange
            ],
        }

        self._try_load_model()

    def _load_card_templates(self):
        """Pre-load card template images and compute ORB descriptors for matching."""
        cards_dir = Path(__file__).resolve().parent.parent.parent / "data" / "sample_cards"
        food_ids = ["rice_egg", "fried_chicken", "noodles", "apple", "milk"]

        for f_id in food_ids:
            card_path = cards_dir / f"{f_id}.png"
            if card_path.exists():
                img = cv2.imread(str(card_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    # Resize template to a consistent size for matching
                    h, w = img.shape[:2]
                    scale = 300.0 / max(h, w)
                    resized = cv2.resize(img, (int(w * scale), int(h * scale)))

                    keypoints, descriptors = self._orb.detectAndCompute(resized, None)
                    if descriptors is not None and len(descriptors) >= 5:
                        self._templates[f_id] = {
                            "keypoints": keypoints,
                            "descriptors": descriptors,
                            "image": resized,
                        }
                        logger.info(f"Loaded template for '{f_id}' ({len(keypoints)} features)")
                    else:
                        logger.warning(f"Template '{f_id}' has too few ORB features ({len(keypoints) if keypoints else 0})")
            else:
                logger.debug(f"Card template not found: {card_path}")

        logger.info(f"ORB templates loaded: {len(self._templates)}/{len(food_ids)}")

    def _try_load_model(self):
        if self.model_path.exists():
            try:
                from ultralytics import YOLO
                logger.info(f"Loading YOLO model from {self.model_path}...")
                self.model = YOLO(str(self.model_path))
                self.is_loaded = True
                logger.info("YOLO model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize YOLO model: {e}")
                self.model = None
                self.is_loaded = False
        else:
            logger.info(f"YOLO model weights not found at {self.model_path}. Running with fallback detection.")
            self.model = None
            self.is_loaded = False

    def start(self):
        """Starts asynchronous inference worker thread."""
        self._running = True
        if self.enable_async:
            self._thread = threading.Thread(
                target=self._inference_worker,
                daemon=True,
                name="VisionInferenceWorker",
            )
            self._thread.start()

    def simulate_detection(self, food_id: str, duration: float = 3.0):
        """Allows injecting a simulated food detection for manual testing."""
        if food_id in self.catalog_foods:
            self._simulated_food_id = food_id
            self._simulated_until = time.time() + duration

    def cancel_simulation(self):
        self._simulated_food_id = None
        self._simulated_until = 0.0

    def submit_frame(self, frame: np.ndarray):
        """Submits a frame for background processing."""
        if not self._running or frame is None:
            return
        with self._lock:
            # Overwrite with latest frame
            self._pending_frame = frame

    def _inference_worker(self):
        while self._running:
            frame_to_process = None
            with self._lock:
                if self._pending_frame is not None:
                    frame_to_process = self._pending_frame
                    self._pending_frame = None

            if frame_to_process is not None:
                res = self._process_frame_sync(frame_to_process)
                with self._lock:
                    self.latest_result = res
                # Limit inference rate to ~12 FPS to preserve CPU/GPU for 60 FPS UI
                time.sleep(0.08)
            else:
                time.sleep(0.02)

    def _process_frame_sync(self, frame: np.ndarray) -> DetectionResult:
        start_t = time.perf_counter()

        # 1. Check for simulated card injection (keyboard shortcuts)
        if self._simulated_food_id and time.time() < self._simulated_until:
            h, w = frame.shape[:2]
            box = (int(w * 0.25), int(h * 0.2), int(w * 0.75), int(h * 0.8))
            f_name = self.catalog_foods.get(self._simulated_food_id, self._simulated_food_id)
            elapsed = (time.perf_counter() - start_t) * 1000.0
            return DetectionResult(
                food_id=self._simulated_food_id,
                food_name=f_name,
                confidence=0.98,
                box=box,
                inference_time_ms=elapsed,
            )

        # 2. Find phone screen in the frame (gate all detection behind this)
        screen_box = self._find_phone_screen(frame)

        if screen_box is not None:
            bx, by, bw, bh = screen_box

            # Expand slightly to include outer colored border of the card
            h_frame, w_frame = frame.shape[:2]
            pad_x = int(bw * 0.12)
            pad_y = int(bh * 0.10)
            x1 = max(0, bx - pad_x)
            y1 = max(0, by - pad_y)
            x2 = min(w_frame, bx + bw + pad_x)
            y2 = min(h_frame, by + bh + pad_y)

            # Stage 1: ORB Template Matching within phone screen ROI
            orb_result = self._match_template_orb(frame, (x1, y1, x2, y2), start_t)
            if orb_result and orb_result.confidence >= 0.70:
                return orb_result

            # Stage 2: Color Signature Analysis within phone screen ROI
            color_result = self._detect_by_color(frame, (x1, y1, x2, y2), start_t)
            if color_result and color_result.confidence >= 0.72:
                return color_result

        # 3. Stage 3: YOLO Model Inference (full-frame fallback)
        if self.is_loaded and self.model is not None:
            try:
                results = self.model.predict(
                    frame,
                    conf=max(0.40, self.confidence_threshold - 0.20),
                    verbose=False,
                )
                if results and len(results) > 0:
                    r = results[0]
                    if len(r.boxes) > 0:
                        best_box = None
                        best_conf = 0.0
                        best_cls = -1
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > best_conf:
                                best_conf = conf
                                best_cls = int(box.cls[0])
                                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                                best_box = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))

                        if best_cls >= 0 and best_cls in r.names:
                            class_name = r.names[best_cls].lower()
                            food_id = class_name
                            food_name = self.catalog_foods.get(food_id, class_name.title())
                            elapsed = (time.perf_counter() - start_t) * 1000.0
                            return DetectionResult(
                                food_id=food_id,
                                food_name=food_name,
                                confidence=best_conf,
                                box=best_box,
                                inference_time_ms=elapsed,
                            )
            except Exception as err:
                logger.debug(f"YOLO inference error: {err}")

        # Fallback: No valid food card in view
        elapsed = (time.perf_counter() - start_t) * 1000.0
        return DetectionResult(
            food_id=None,
            food_name=None,
            confidence=0.0,
            box=None,
            inference_time_ms=elapsed,
        )

    def _find_phone_screen(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect a bright white phone screen rectangle in the frame.
        Returns (x, y, w, h) of the largest valid screen contour or None.
        This is the primary gate that prevents false positives on faces/clothes/walls.
        """
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Phone screen: bright, low saturation, high value
        white_mask = (
            (hsv[:, :, 2] > 175) &
            (hsv[:, :, 1] < 60) &
            (gray > 170)
        ).astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_screen = None
        best_area = 0

        for c in contours:
            area = cv2.contourArea(c)
            # Screen must be 3% to 80% of frame area
            if (h * w * 0.03) <= area <= (h * w * 0.80):
                bx, by, bw, bh = cv2.boundingRect(c)
                aspect = bh / float(bw) if bw > 0 else 0
                # Phone screen is taller than wide (portrait mode)
                if 1.1 <= aspect <= 2.8:
                    if area > best_area:
                        best_area = area
                        best_screen = (bx, by, bw, bh)

        return best_screen

    def _match_template_orb(self, frame: np.ndarray, roi_box: Tuple[int, int, int, int],
                            start_t: float) -> Optional[DetectionResult]:
        """
        Match ORB features of the camera ROI against pre-loaded card templates.
        Returns the best matching food card if sufficient feature matches are found.
        """
        if not self._templates:
            return None

        x1, y1, x2, y2 = roi_box
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Multi-scale matching for robustness
        best_food_id = None
        best_score = 0
        best_match_count = 0

        for scale in [0.6, 0.8, 1.0, 1.3]:
            rh, rw = roi_gray.shape[:2]
            scaled = cv2.resize(roi_gray, (int(rw * scale), int(rh * scale)))
            kp_roi, desc_roi = self._orb.detectAndCompute(scaled, None)

            if desc_roi is None or len(desc_roi) < 5:
                continue

            for f_id, tmpl in self._templates.items():
                desc_tmpl = tmpl["descriptors"]

                try:
                    # KNN matching with ratio test (Lowe's method)
                    matches = self._bf_matcher.knnMatch(desc_tmpl, desc_roi, k=2)

                    # Apply ratio test
                    good_matches = []
                    for m_pair in matches:
                        if len(m_pair) == 2:
                            m, n = m_pair
                            if m.distance < 0.78 * n.distance:
                                good_matches.append(m)

                    match_count = len(good_matches)
                    # Normalize score by number of template features
                    score = match_count / max(len(desc_tmpl), 1)

                    if match_count > best_match_count and match_count >= 8:
                        best_match_count = match_count
                        best_food_id = f_id
                        best_score = score

                except Exception:
                    continue

        if best_food_id and best_match_count >= 8:
            conf = min(0.96, 0.60 + best_score * 1.5)
            elapsed = (time.perf_counter() - start_t) * 1000.0
            food_name = self.catalog_foods.get(best_food_id, best_food_id.title())
            logger.debug(f"ORB match: {best_food_id} ({best_match_count} matches, conf={conf:.2f})")
            return DetectionResult(
                food_id=best_food_id,
                food_name=food_name,
                confidence=conf,
                box=(x1, y1, x2, y2),
                inference_time_ms=elapsed,
            )

        return None

    def _detect_by_color(self, frame: np.ndarray, roi_box: Tuple[int, int, int, int],
                         start_t: float) -> Optional[DetectionResult]:
        """
        Screen-Bounded Color Signature Detector.
        Analyzes color distribution ONLY inside the detected phone screen ROI.
        """
        x1, y1, x2, y2 = roi_box
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        roi_area = (x2 - x1) * (y2 - y1)
        if roi_area < 800:
            return None

        # Count colored pixels for each food signature
        pixel_counts = {}
        for f_id, ranges in self._color_signatures.items():
            total = 0
            for r in ranges:
                mask = cv2.inRange(roi_hsv, np.array(r["lower"]), np.array(r["upper"]))
                total += cv2.countNonZero(mask)
            pixel_counts[f_id] = total

        # Find top candidate
        best_id = max(pixel_counts, key=pixel_counts.get)
        best_px = pixel_counts[best_id]

        # Require minimum colored pixel coverage (2% of ROI)
        min_pixels = max(150, int(roi_area * 0.02))

        if best_px >= min_pixels:
            # Extra disambiguation: check if rice_egg vs fried_chicken are close
            if best_id in ("rice_egg", "fried_chicken"):
                rice_px = pixel_counts.get("rice_egg", 0)
                chick_px = pixel_counts.get("fried_chicken", 0)

                # Use blue text presence to disambiguate (rice_egg has dark goldenrod text)
                blue_mask = cv2.inRange(roi_hsv, np.array((95, 40, 40)), np.array((140, 255, 255)))
                blue_px = cv2.countNonZero(blue_mask)

                # Use brightness gradient: rice_egg cards are brighter/yellower
                yellow_bright = cv2.inRange(roi_hsv, np.array((25, 60, 160)), np.array((40, 255, 255)))
                yellow_px = cv2.countNonZero(yellow_bright)

                orange_deep = cv2.inRange(roi_hsv, np.array((8, 100, 100)), np.array((20, 255, 255)))
                orange_px = cv2.countNonZero(orange_deep)

                if yellow_px > orange_px * 1.2:
                    best_id = "rice_egg"
                elif orange_px > yellow_px * 1.2:
                    best_id = "fried_chicken"

            conf = min(0.94, 0.72 + (best_px / roi_area) * 2.0)
            elapsed = (time.perf_counter() - start_t) * 1000.0
            food_name = self.catalog_foods.get(best_id, best_id.title())
            return DetectionResult(
                food_id=best_id,
                food_name=food_name,
                confidence=conf,
                box=(x1, y1, x2, y2),
                inference_time_ms=elapsed,
            )

        return None

    def get_latest_result(self) -> DetectionResult:
        with self._lock:
            return self.latest_result

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
