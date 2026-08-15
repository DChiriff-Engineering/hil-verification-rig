import pytest

from hil.protocol import FrameError, SensorFrame, crc16_ccitt_false, decode_sensor_frame, encode_sensor_frame


def test_crc16_ccitt_false_matches_standard_check_vector():
    assert crc16_ccitt_false(b"123456789") == 0x29B1


def test_sensor_frame_round_trip_preserves_integer_engineering_units():
    frame = SensorFrame(sequence=0x1234, bus_mv=12050, current_ma=4321, temperature_cc=7123, flags=0x05)
    encoded = encode_sensor_frame(frame)
    assert len(encoded) == 14
    assert decode_sensor_frame(encoded) == frame


def test_sensor_frame_rejects_corrupt_crc():
    encoded = bytearray(encode_sensor_frame(SensorFrame(7, 12000, 1000, 2500)))
    encoded[8] ^= 0x01
    with pytest.raises(FrameError, match="CRC"):
        decode_sensor_frame(bytes(encoded))


def test_sensor_frame_rejects_wrong_protocol_version():
    encoded = bytearray(encode_sensor_frame(SensorFrame(1, 12000, 1000, 2500)))
    encoded[2] = 2
    crc = crc16_ccitt_false(encoded[:-2])
    encoded[-2:] = crc.to_bytes(2, "little")
    with pytest.raises(FrameError, match="version"):
        decode_sensor_frame(bytes(encoded))
