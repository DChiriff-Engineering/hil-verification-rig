import time
import pytest

from hil.hardware import PhysicalRig

pytestmark = pytest.mark.hil


@pytest.fixture(scope="module")
def rig():
    active = PhysicalRig.discover()
    yield active
    active.close()


def test_all_three_roles_are_uniquely_identified(rig):
    assert set(rig.identities) == {"dut", "hil", "witness"}
    assert len({identity.board_id for identity in rig.identities.values()}) == 3


def test_boot_reset_is_safe(rig):
    rig.dut.reset()
    status = rig.dut.status()
    assert status["state"] == "STARTUP"
    assert status["enable"] is False


def test_nominal_physical_closed_loop_reaches_operating_state(rig):
    rig.hil.clear_fault()
    rig.hil.set_load(2000)
    rig.dut.reset()
    time.sleep(0.4)
    status = rig.dut.status()
    assert status["state"] in {"NORMAL", "DERATE"}
    assert status["enable"] is True


def test_overvoltage_injection_drives_safe_fault(rig):
    rig.hil.set_fault("OVERVOLTAGE", value=15000)
    time.sleep(0.2)
    status = rig.dut.status()
    try:
        assert status["state"] == "FAULT"
        assert status["fault"] == "OVERVOLTAGE"
        assert status["enable"] is False
    finally:
        rig.hil.clear_fault()


def test_sensor_dropout_triggers_timeout(rig):
    rig.hil.set_fault("DROPOUT", value=1)
    time.sleep(0.35)
    status = rig.dut.status()
    try:
        assert status["state"] == "FAULT"
        assert status["fault"] == "SENSOR_TIMEOUT"
    finally:
        rig.hil.clear_fault()


def test_uno_witness_agrees_with_hil_enable_observation(rig):
    time.sleep(0.05)
    witness = rig.witness.sample()
    hil = rig.hil.status()
    assert witness["enable"] == int(bool(hil["enable_observed"]))
