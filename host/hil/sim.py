from __future__ import annotations

from dataclasses import dataclass

from .models import DutState, FaultReason
from .protocol import FrameError, SensorFrame, decode_sensor_frame

UV_MV = 10500
RECOVERY_MIN_MV = 10800
OV_MV = 14500
OC_WARN_MA = 4500
OC_SEVERE_MA = 6000
OC_SEVERE_SAMPLES = 3
TEMP_DERATE_CC = 7000
TEMP_SEVERE_CC = 8500
SENSOR_TIMEOUT_MS = 250
RECOVERY_DWELL_MS = 1000
INVALID_LIMIT = 3


@dataclass(slots=True)
class DutCounters:
    bad_frames: int = 0
    stale_sequences: int = 0
    timeouts: int = 0
    overcurrent_faults: int = 0
    overtemperature_faults: int = 0
    overvoltage_faults: int = 0
    recoveries: int = 0
    sequence_gaps: int = 0


class VirtualDut:
    """Deterministic reference model for host regression; not physical evidence."""

    def __init__(self) -> None:
        self.state = DutState.STARTUP
        self.fault_reason = FaultReason.NONE
        self.enable = False
        self.fan_percent = 0
        self.counters = DutCounters()
        self.last_valid_ms: int | None = None
        self.last_sequence: int | None = None
        self.consecutive_invalid = 0
        self.severe_oc_count = 0
        self.recovery_start_ms: int | None = None
        self.last_frame: SensorFrame | None = None

    def _fault(self, reason: FaultReason) -> None:
        if self.state is not DutState.FAULT or self.fault_reason is not reason:
            if reason is FaultReason.OVERCURRENT:
                self.counters.overcurrent_faults += 1
            elif reason is FaultReason.OVERTEMPERATURE:
                self.counters.overtemperature_faults += 1
            elif reason is FaultReason.OVERVOLTAGE:
                self.counters.overvoltage_faults += 1
        self.state = DutState.FAULT
        self.fault_reason = reason
        self.enable = False
        self.fan_percent = 100
        self.recovery_start_ms = None

    @staticmethod
    def _is_recovery_healthy(frame: SensorFrame) -> bool:
        return (
            frame.bus_mv >= RECOVERY_MIN_MV
            and frame.bus_mv < OV_MV
            and frame.current_ma < OC_WARN_MA
            and frame.temperature_cc < TEMP_DERATE_CC
        )

    def _implausible_slew(self, frame: SensorFrame) -> bool:
        if self.last_frame is None:
            return False
        dv = abs(frame.bus_mv - self.last_frame.bus_mv)
        di = abs(frame.current_ma - self.last_frame.current_ma)
        dt = abs(frame.temperature_cc - self.last_frame.temperature_cc)
        bus_bad = frame.bus_mv < OV_MV and dv > 3000
        current_bad = frame.current_ma < OC_SEVERE_MA and di > 4000
        temp_bad = frame.temperature_cc < TEMP_SEVERE_CC and dt > 1500
        return bus_bad or current_bad or temp_bad

    def _apply_valid_frame(self, frame: SensorFrame, now_ms: int) -> None:
        if frame.bus_mv >= OV_MV:
            self._fault(FaultReason.OVERVOLTAGE)
            return
        if frame.temperature_cc >= TEMP_SEVERE_CC:
            self._fault(FaultReason.OVERTEMPERATURE)
            return

        self.severe_oc_count = self.severe_oc_count + 1 if frame.current_ma >= OC_SEVERE_MA else 0
        if self.severe_oc_count >= OC_SEVERE_SAMPLES:
            self._fault(FaultReason.OVERCURRENT)
            return
        if self._implausible_slew(frame):
            self._fault(FaultReason.IMPLAUSIBLE_SLEW)
            return

        if self.state in (DutState.FAULT, DutState.RECOVERY):
            if self._is_recovery_healthy(frame):
                if self.state is DutState.FAULT:
                    self.state = DutState.RECOVERY
                    self.recovery_start_ms = now_ms
                elif self.recovery_start_ms is not None and now_ms - self.recovery_start_ms >= RECOVERY_DWELL_MS:
                    self.state = DutState.NORMAL
                    self.fault_reason = FaultReason.NONE
                    self.enable = True
                    self.fan_percent = 25
                    self.recovery_start_ms = None
                    self.counters.recoveries += 1
            else:
                self.state = DutState.FAULT
                self.enable = False
                self.fan_percent = 100
                self.recovery_start_ms = None
            return

        derate = frame.bus_mv < UV_MV or frame.current_ma >= OC_WARN_MA or frame.temperature_cc >= TEMP_DERATE_CC
        self.state = DutState.DERATE if derate else DutState.NORMAL
        self.fault_reason = FaultReason.NONE
        self.enable = True
        if frame.temperature_cc >= TEMP_DERATE_CC:
            span = max(1, TEMP_SEVERE_CC - TEMP_DERATE_CC)
            self.fan_percent = min(100, 40 + (frame.temperature_cc - TEMP_DERATE_CC) * 60 // span)
        elif frame.current_ma >= OC_WARN_MA or frame.bus_mv < UV_MV:
            self.fan_percent = 70
        else:
            self.fan_percent = 25

    def ingest(self, payload: bytes, now_ms: int) -> None:
        try:
            frame = decode_sensor_frame(payload)
        except FrameError:
            self.counters.bad_frames += 1
            self.consecutive_invalid += 1
            if self.consecutive_invalid >= INVALID_LIMIT:
                self._fault(FaultReason.DATA_INTEGRITY)
            return

        if self.last_sequence is not None:
            delta = (frame.sequence - self.last_sequence) & 0xFFFF
            if delta == 0 or delta > 0x7FFF:
                self.counters.stale_sequences += 1
                self.consecutive_invalid += 1
                if self.consecutive_invalid >= INVALID_LIMIT:
                    self._fault(FaultReason.STALE_SEQUENCE)
                return
            if delta > 1:
                self.counters.sequence_gaps += delta - 1

        self.consecutive_invalid = 0
        self.last_sequence = frame.sequence
        self.last_valid_ms = now_ms
        self._apply_valid_frame(frame, now_ms)
        self.last_frame = frame

    def tick(self, now_ms: int) -> None:
        if self.last_valid_ms is not None and now_ms - self.last_valid_ms > SENSOR_TIMEOUT_MS:
            if self.state is not DutState.FAULT or self.fault_reason is not FaultReason.SENSOR_TIMEOUT:
                self.counters.timeouts += 1
            self._fault(FaultReason.SENSOR_TIMEOUT)
