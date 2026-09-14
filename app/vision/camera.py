"""
Threaded Camera Manager.
Captures laptop webcam frames asynchronously to ensure zero UI frame drops.
"""
import logging
import threading
import time
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("pet.camera")


class CameraManager:
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
    ):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height

        self.cap = None
        self.last_frame: Optional[np.ndarray] = None
        self.is_connected = False
        self._running = False
        self._lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Starts camera capture thread."""
        try:
            import cv2
            # Use CAP_DSHOW on Windows for fast webcam initialization
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to standard capture
                self.cap = cv2.VideoCapture(self.camera_index)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                self.is_connected = True
                logger.info(f"Webcam opened on index {self.camera_index}")
            else:
                logger.warning(f"Could not open webcam index {self.camera_index}. Using fallback placeholder.")
                self.is_connected = False
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            self.is_connected = False

        self._running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True, name="CameraCaptureThread")
        self.thread.start()
        return self.is_connected

    def _generate_fallback_frame(self) -> np.ndarray:
        """Generates a pleasant synthetic camera frame if real camera is offline."""
        img = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        # Gradient background
        for y in range(self.target_height):
            img[y, :, :] = [40, 30 + int(y * 0.05), 50 + int(y * 0.08)]

        try:
            import cv2
            cv2.putText(
                img,
                "Camera Offline / Simulated Mode",
                (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (200, 200, 255),
                2,
            )
            cv2.putText(
                img,
                "Show food or press 1-5 to simulate cards",
                (30, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (180, 220, 180),
                1,
            )
            # Center target box
            box_w, box_h = 240, 280
            cx, cy = self.target_width // 2, self.target_height // 2 + 20
            cv2.rectangle(
                img,
                (cx - box_w // 2, cy - box_h // 2),
                (cx + box_w // 2, cy + box_h // 2),
                (100, 180, 255),
                2,
            )
            cv2.putText(
                img,
                "[ HOLD CARD HERE ]",
                (cx - 90, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (120, 190, 255),
                1,
            )
        except Exception:
            pass

        return img

    def _capture_loop(self):
        while self._running:
            if self.is_connected and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Mirror webcam frame horizontally for natural UX
                    frame = np.ascontiguousarray(np.fliplr(frame))
                    with self._lock:
                        self.last_frame = frame
                else:
                    time.sleep(0.03)
            else:
                fallback = self._generate_fallback_frame()
                with self._lock:
                    self.last_frame = fallback
                time.sleep(0.05)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the latest captured BGR frame safely."""
        with self._lock:
            if self.last_frame is not None:
                return True, self.last_frame.copy()
            return False, None

    def stop(self):
        self._running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.is_connected = False
