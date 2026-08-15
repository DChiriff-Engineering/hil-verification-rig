from __future__ import annotations

import json
from typing import Any

from .transports import LineTransport


class DeviceProtocolError(RuntimeError):
    pass


class _JsonDevice:
    def __init__(self, transport: LineTransport) -> None:
        self.transport = transport

    def _command(self, line: str) -> dict[str, Any]:
        self.transport.write_line(line)
        try:
            response = json.loads(self.transport.read_line())
        except (json.JSONDecodeError, TimeoutError) as exc:
            raise DeviceProtocolError(f"invalid response to {line!r}") from exc
        if not response.get("ok", False):
            raise DeviceProtocolError(str(response.get("message", f"command failed: {line}")))
        return response


class DutDevice(_JsonDevice):
    def status(self) -> dict[str, Any]:
        return self._command("STATUS?")

    def reset(self) -> dict[str, Any]:
        return self._command("RESET")


class HilDevice(_JsonDevice):
    def status(self) -> dict[str, Any]:
        return self._command("STATUS?")

    def set_fault(self, kind: str, *, value: int) -> dict[str, Any]:
        return self._command(f"FAULT SET {kind} {value}")

    def clear_fault(self) -> dict[str, Any]:
        return self._command("FAULT CLEAR")

    def set_load(self, milliamps: int) -> dict[str, Any]:
        return self._command(f"LOAD {milliamps}")


class WitnessDevice(_JsonDevice):
    def sample(self) -> dict[str, Any]:
        return self._command("SAMPLE?")
