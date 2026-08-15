from __future__ import annotations

from collections import deque
from typing import Iterable, Protocol


class LineTransport(Protocol):
    def write_line(self, line: str) -> None: ...
    def read_line(self) -> str: ...
    def close(self) -> None: ...


class MemoryLineTransport:
    def __init__(self, reads: Iterable[str] = ()) -> None:
        self.reads = deque(reads)
        self.writes: list[str] = []
        self.closed = False

    def write_line(self, line: str) -> None:
        if self.closed:
            raise RuntimeError("transport is closed")
        self.writes.append(line)

    def read_line(self) -> str:
        if self.closed:
            raise RuntimeError("transport is closed")
        if not self.reads:
            raise TimeoutError("no queued line")
        return self.reads.popleft()

    def close(self) -> None:
        self.closed = True


class SerialLineTransport:
    def __init__(self, port: str, *, baudrate: int = 115200, timeout_s: float = 0.5) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("pySerial is required for physical serial transports") from exc
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout_s, write_timeout=timeout_s)

    def write_line(self, line: str) -> None:
        self._serial.write((line.rstrip("\r\n") + "\n").encode("utf-8"))
        self._serial.flush()

    def read_line(self) -> str:
        raw = self._serial.readline()
        if not raw:
            raise TimeoutError("serial read timed out")
        return raw.decode("utf-8").strip()

    def close(self) -> None:
        self._serial.close()
