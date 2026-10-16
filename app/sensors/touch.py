"""Serial touch input for a TTP223 connected through an Arduino or ESP32."""
import logging
import queue
import threading
import time
from typing import Optional

import serial

logger = logging.getLogger("pet.touch")


class TouchSensorError(RuntimeError):
    """Raised when the touch sensor cannot be started."""


class TouchSensor:
    def __init__(
        self,
        port: str,
        baud_rate: int = 9600,
        debounce_seconds: float = 0.4,
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.debounce_seconds = debounce_seconds
        self._events: queue.Queue[None] = queue.Queue()
        self._stop_event = threading.Event()
        self._serial: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._last_touch_time = float("-inf")

    def start(self) -> None:
        """Open the serial port and start reading touch messages in a thread."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.1,
            )
        except serial.SerialException as exc:
            raise TouchSensorError(
                f"Could not open touch sensor on {self.port}: {exc}"
            ) from exc

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
            name="TouchSensorThread",
        )
        self._thread.start()
        logger.info("Touch sensor connected on %s", self.port)

    def _read_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw_line = self._serial.readline()
            except serial.SerialException:
                logger.exception("Lost touch sensor connection on %s", self.port)
                self._stop_event.set()
                return

            message = raw_line.decode("utf-8", errors="replace").strip()
            self._handle_message(message)

    def _handle_message(self, message: str, now: Optional[float] = None) -> None:
        if message != "TOUCH":
            return

        touch_time = time.monotonic() if now is None else now
        if touch_time - self._last_touch_time < self.debounce_seconds:
            return

        self._last_touch_time = touch_time
        self._events.put_nowait(None)

    def poll_touch(self) -> bool:
        """Return immediately, consuming at most one queued touch event."""
        try:
            self._events.get_nowait()
        except queue.Empty:
            return False
        return True

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            self._serial.close()
        logger.info("Touch sensor stopped")
