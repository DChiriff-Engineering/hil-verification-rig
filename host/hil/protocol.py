from __future__ import annotations

from dataclasses import dataclass
import struct

SYNC_WORD = 0xA55A
PROTOCOL_VERSION = 1
_FRAME_NO_CRC = struct.Struct("<HBBHHHh")
FRAME_SIZE = _FRAME_NO_CRC.size + 2


class FrameError(ValueError):
    """Raised when a sensor frame violates the versioned wire contract."""


@dataclass(frozen=True, slots=True)
class SensorFrame:
    sequence: int
    bus_mv: int
    current_ma: int
    temperature_cc: int
    flags: int = 0


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def _validate_frame_fields(frame: SensorFrame) -> None:
    if not 0 <= frame.sequence <= 0xFFFF:
        raise ValueError("sequence must fit uint16")
    if not 0 <= frame.bus_mv <= 0xFFFF:
        raise ValueError("bus_mv must fit uint16")
    if not 0 <= frame.current_ma <= 0xFFFF:
        raise ValueError("current_ma must fit uint16")
    if not -32768 <= frame.temperature_cc <= 32767:
        raise ValueError("temperature_cc must fit int16")
    if not 0 <= frame.flags <= 0xFF:
        raise ValueError("flags must fit uint8")


def encode_sensor_frame(frame: SensorFrame) -> bytes:
    _validate_frame_fields(frame)
    body = _FRAME_NO_CRC.pack(
        SYNC_WORD,
        PROTOCOL_VERSION,
        frame.flags,
        frame.sequence,
        frame.bus_mv,
        frame.current_ma,
        frame.temperature_cc,
    )
    return body + struct.pack("<H", crc16_ccitt_false(body))


def decode_sensor_frame(data: bytes) -> SensorFrame:
    if len(data) != FRAME_SIZE:
        raise FrameError(f"frame length {len(data)} != {FRAME_SIZE}")
    body, crc_bytes = data[:-2], data[-2:]
    received_crc = struct.unpack("<H", crc_bytes)[0]
    expected_crc = crc16_ccitt_false(body)
    if received_crc != expected_crc:
        raise FrameError(f"CRC mismatch: received 0x{received_crc:04X}, expected 0x{expected_crc:04X}")
    sync, version, flags, sequence, bus_mv, current_ma, temperature_cc = _FRAME_NO_CRC.unpack(body)
    if sync != SYNC_WORD:
        raise FrameError(f"sync mismatch: 0x{sync:04X}")
    if version != PROTOCOL_VERSION:
        raise FrameError(f"unsupported protocol version {version}")
    return SensorFrame(sequence, bus_mv, current_ma, temperature_cc, flags)
