import json

from hil.discovery import scan_system_ports
from hil.transports import MemoryLineTransport


def test_system_scan_ignores_nonrig_ports_and_keeps_three_roles():
    responses = {
        "COM1": ["not-json"],
        "COM4": [json.dumps({"type":"id","ok":True,"protocol_version":1,"role":"dut","firmware_version":"0.1.0","board_id":"D"})],
        "COM7": [json.dumps({"type":"id","ok":True,"protocol_version":1,"role":"hil","firmware_version":"0.1.0","board_id":"H"})],
        "COM9": [json.dumps({"type":"id","ok":True,"protocol_version":1,"role":"witness","firmware_version":"0.1.0","board_id":"W"})],
    }
    created = {}
    def factory(port):
        tr = MemoryLineTransport(responses[port])
        created[port] = tr
        return tr
    found, transports = scan_system_ports(list(responses), transport_factory=factory)
    assert set(found) == {"dut","hil","witness"}
    assert created["COM1"].closed is True
    assert transports["dut"] is created["COM4"]
    assert transports["hil"] is created["COM7"]
    assert transports["witness"] is created["COM9"]
