"""
Temporal Detection Stabilizer.
Prevents false positives from single unstable camera frames.
Requires consistent consecutive detections meeting confidence threshold.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class StabilizedDetection:
    food_id: str
    confidence: float
    consecutive_count: int
    is_confirmed: bool
    box: Optional[tuple] = None  # (x1, y1, x2, y2)


class TemporalStabilizer:
    def __init__(
        self,
        required_consecutive_frames: int = 5,
        confidence_threshold: float = 0.70,
    ):
        self.required_consecutive_frames = required_consecutive_frames
        self.confidence_threshold = confidence_threshold

        self.current_candidate_id: Optional[str] = None
        self.consecutive_count: int = 0
        self.confirmed_id: Optional[str] = None
        self.highest_conf: float = 0.0
        self.last_box: Optional[tuple] = None
        self.empty_frames_count: int = 0

    def update(
        self,
        detected_id: Optional[str],
        confidence: float = 0.0,
        box: Optional[tuple] = None,
    ) -> StabilizedDetection:
        """
        Feed frame-by-frame detection result.
        Returns StabilizedDetection with confirmation status.
        """
        if detected_id is not None and confidence >= self.confidence_threshold:
            self.empty_frames_count = 0
            if detected_id == self.current_candidate_id:
                self.consecutive_count += 1
                self.highest_conf = max(self.highest_conf, confidence)
                self.last_box = box or self.last_box
            else:
                # Switched to a different food candidate
                self.current_candidate_id = detected_id
                self.consecutive_count = 1
                self.highest_conf = confidence
                self.last_box = box

            is_confirmed = self.consecutive_count >= self.required_consecutive_frames
            if is_confirmed:
                self.confirmed_id = self.current_candidate_id

            return StabilizedDetection(
                food_id=self.current_candidate_id,
                confidence=self.highest_conf,
                consecutive_count=self.consecutive_count,
                is_confirmed=is_confirmed,
                box=self.last_box,
            )
        else:
            # No valid detection in this frame
            self.empty_frames_count += 1
            # If 3 consecutive empty frames occur, reset candidate
            if self.empty_frames_count >= 3:
                self.current_candidate_id = None
                self.consecutive_count = 0
                self.highest_conf = 0.0
                self.last_box = None
                self.confirmed_id = None

            return StabilizedDetection(
                food_id="",
                confidence=0.0,
                consecutive_count=0,
                is_confirmed=False,
                box=None,
            )

    def reset(self):
        """Reset stabilizer state."""
        self.current_candidate_id = None
        self.consecutive_count = 0
        self.confirmed_id = None
        self.highest_conf = 0.0
        self.last_box = None
        self.empty_frames_count = 0
