import json

from hil.devices import DutDevice, HilDevice, WitnessDevice
from hil.transports import MemoryLineTransport


def test_dut_status_command_returns_structured_json():
    tr = MemoryLineTransport([json.dumps({"type":"status","ok":True,"state":"NORMAL","enable":True,"fan_percent":25})])
    dut = DutDevice(tr)
    assert dut.status()["state"] == "NORMAL"
    assert tr.writes == ["STATUS?"]


def test_hil_fault_commands_are_explicit():
    tr = MemoryLineTransport([json.dumps({"type":"ack","ok":True,"cmd":"FAULT SET","fault":"OVERVOLTAGE"}), json.dumps({"type":"ack","ok":True,"cmd":"FAULT CLEAR"})])
    dev = HilDevice(tr)
    dev.set_fault("OVERVOLTAGE", value=15000)
    dev.clear_fault()
    assert tr.writes == ["FAULT SET OVERVOLTAGE 15000", "FAULT CLEAR"]


def test_witness_is_read_only_at_host_api_level():
    tr = MemoryLineTransport([json.dumps({"type":"witness","ok":True,"enable":1,"fault":0,"timestamp_ms":10})])
    witness = WitnessDevice(tr)
    assert witness.sample()["enable"] == 1
    assert not hasattr(witness, "set_output")
