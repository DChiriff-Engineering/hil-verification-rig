from hil.models import DutState, FaultReason
from hil.protocol import SensorFrame, encode_sensor_frame
from hil.sim import VirtualDut


def send(dut, now_ms, seq, v=12000, i=1000, t=2500):
    return dut.ingest(encode_sensor_frame(SensorFrame(seq, v, i, t)), now_ms)


def test_boot_is_safe_until_first_valid_healthy_frame():
    dut = VirtualDut()
    assert dut.state is DutState.STARTUP
    assert dut.enable is False
    send(dut, 0, 0)
    assert dut.state is DutState.NORMAL
    assert dut.enable is True


def test_uv_boundary_is_exact_and_enters_derate_below_threshold():
    dut = VirtualDut()
    send(dut, 0, 0, v=10500)
    assert dut.state is DutState.NORMAL
    send(dut, 50, 1, v=10499)
    assert dut.state is DutState.DERATE


def test_severe_overvoltage_faults_immediately():
    dut = VirtualDut()
    send(dut, 0, 0)
    send(dut, 50, 1, v=14500)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.OVERVOLTAGE
    assert dut.enable is False


def test_severe_overcurrent_requires_three_valid_samples():
    dut = VirtualDut()
    send(dut, 0, 0)
    send(dut, 50, 1, i=6000)
    send(dut, 100, 2, i=6000)
    assert dut.state is DutState.DERATE
    send(dut, 150, 3, i=6000)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.OVERCURRENT


def test_thermal_warning_derates_and_severe_temperature_faults():
    dut = VirtualDut()
    temperatures = [2500, 3500, 4500, 5500, 6500, 7000]
    for seq, temperature in enumerate(temperatures):
        send(dut, seq * 50, seq, t=temperature)
    assert dut.state is DutState.DERATE
    warning_pwm = dut.fan_percent
    send(dut, 300, 6, t=8000)
    assert dut.fan_percent >= warning_pwm
    send(dut, 350, 7, t=8500)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.OVERTEMPERATURE


def test_three_consecutive_bad_crc_frames_escalate_to_fault():
    dut = VirtualDut()
    good = encode_sensor_frame(SensorFrame(0, 12000, 1000, 2500))
    dut.ingest(good, 0)
    for n in range(3):
        corrupt = bytearray(encode_sensor_frame(SensorFrame(n + 1, 12000, 1000, 2500)))
        corrupt[6] ^= 0x01
        dut.ingest(bytes(corrupt), 50 * (n + 1))
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.DATA_INTEGRITY


def test_three_repeated_sequences_escalate_to_fault():
    dut = VirtualDut()
    send(dut, 0, 10)
    send(dut, 50, 10)
    send(dut, 100, 10)
    send(dut, 150, 10)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.STALE_SEQUENCE


def test_sensor_timeout_fails_safe_after_250_ms():
    dut = VirtualDut()
    send(dut, 0, 0)
    dut.tick(250)
    assert dut.state is DutState.NORMAL
    dut.tick(251)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.SENSOR_TIMEOUT


def test_fault_recovery_requires_full_healthy_dwell():
    dut = VirtualDut()
    send(dut, 0, 0)
    send(dut, 50, 1, v=14500)
    assert dut.state is DutState.FAULT
    send(dut, 100, 2, v=12000)
    assert dut.state is DutState.RECOVERY
    for k in range(3, 22):
        send(dut, 50 * k, k, v=12000)
    assert dut.state is DutState.RECOVERY
    send(dut, 1100, 22, v=12000)
    assert dut.state is DutState.NORMAL
    assert dut.enable is True


def test_isolated_bad_crc_does_not_poison_following_valid_sequence_gap():
    dut = VirtualDut()
    send(dut, 0, 0)
    corrupt = bytearray(encode_sensor_frame(SensorFrame(1, 12000, 1000, 2500)))
    corrupt[6] ^= 0x01
    dut.ingest(bytes(corrupt), 50)
    send(dut, 100, 2)
    assert dut.state is DutState.NORMAL
    assert dut.counters.bad_frames == 1
    assert dut.counters.stale_sequences == 0


def test_implausible_nonsevere_slew_faults_but_severe_fault_reason_has_priority():
    dut = VirtualDut()
    send(dut, 0, 0, v=12000, i=1000, t=2500)
    send(dut, 50, 1, v=12000, i=5500, t=2500)
    assert dut.state is DutState.FAULT
    assert dut.fault_reason is FaultReason.IMPLAUSIBLE_SLEW

    dut2 = VirtualDut()
    send(dut2, 0, 0, t=2500)
    send(dut2, 50, 1, t=8500)
    assert dut2.fault_reason is FaultReason.OVERTEMPERATURE
