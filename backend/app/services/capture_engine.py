from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class FramePacket:
    frame_id: int
    timestamp: float
    data: Any


class FreshestFrameBuffer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._packet: FramePacket | None = None

    def set(self, packet: FramePacket) -> None:
        with self._lock:
            self._packet = packet

    def get(self) -> FramePacket | None:
        with self._lock:
            return self._packet


class CaptureEngine:
    """Thread A fetches frames continuously; Thread B consumes freshest packet."""

    def __init__(self, fps: int = 30) -> None:
        self.fps = fps
        self.buffer = FreshestFrameBuffer()
        self._running = False
        self._thread: threading.Thread | None = None
        self._frame_id = 0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def consume_latest(self) -> FramePacket | None:
        return self.buffer.get()

    def _fetch_loop(self) -> None:
        interval = 1.0 / max(self.fps, 1)
        while self._running:
            self._frame_id += 1
            packet = FramePacket(frame_id=self._frame_id, timestamp=time.time(), data={"synthetic": True})
            self.buffer.set(packet)
            time.sleep(interval)
