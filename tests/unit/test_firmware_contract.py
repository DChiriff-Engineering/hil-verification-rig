from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def define_int(source: str, name: str) -> int:
    match = re.search(rf"#define\s+{name}\s+(\d+)", source)
    assert match, f"missing {name}"
    return int(match.group(1))


def test_shared_firmware_protocol_matches_frozen_host_constants():
    header = text("firmware/common/hil_protocol.h")
    assert "#define HIL_SYNC_WORD 0xA55Au" in header
    assert define_int(header, "HIL_PROTOCOL_VERSION") == 1
    assert define_int(header, "HIL_UV_MV") == 10500
    assert define_int(header, "HIL_RECOVERY_MIN_MV") == 10800
    assert define_int(header, "HIL_OV_MV") == 14500
    assert define_int(header, "HIL_OC_WARN_MA") == 4500
    assert define_int(header, "HIL_OC_SEVERE_MA") == 6000
    assert define_int(header, "HIL_TEMP_DERATE_CC") == 7000
    assert define_int(header, "HIL_TEMP_SEVERE_CC") == 8500
    assert define_int(header, "HIL_SENSOR_TIMEOUT_MS") == 250
    assert define_int(header, "HIL_RECOVERY_DWELL_MS") == 1000


def test_dut_pin_contract_uses_uart_rx_and_three_physical_outputs():
    source = text("firmware/dut_pico/src/main.c")
    assert "#define SENSOR_UART_RX_PIN 1u" in source
    assert "#define ENABLE_PIN 10u" in source
    assert "#define FAN_PWM_PIN 11u" in source
    assert "#define FAULT_STATUS_PIN 12u" in source


def test_hil_pin_contract_observes_dut_outputs_and_transmits_uart():
    source = text("firmware/hil_pico/src/main.c")
    assert "#define SENSOR_UART_TX_PIN 0u" in source
    assert "#define DUT_ENABLE_PIN 10u" in source
    assert "#define DUT_PWM_PIN 11u" in source


def test_uno_witness_never_configures_a_pico_connected_signal_as_output():
    source = text("firmware/witness_uno/witness_uno.ino")
    assert "pinMode" in source
    assert "OUTPUT" not in source


def test_dut_sequence_policy_allows_forward_gaps_but_rejects_repeat_or_backward():
    source = text("firmware/dut_pico/src/main.c")
    assert "uint16_t delta = (uint16_t)(f.sequence - last_sequence);" in source
    assert "delta == 0u || delta > 0x7fffu" in source


def test_dut_slew_check_is_after_primary_severe_fault_checks():
    source = text("firmware/dut_pico/src/main.c")
    ov = source.index("f->bus_mv >= HIL_OV_MV")
    temp = source.index("f->temperature_cc >= HIL_TEMP_SEVERE_CC")
    slew = source.index("implausible_slew(f)")
    assert ov < slew and temp < slew
