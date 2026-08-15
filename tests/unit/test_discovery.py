import json

import pytest

from hil.discovery import DiscoveryError, discover_roles
from hil.transports import MemoryLineTransport


def make(role, board_id):
    return MemoryLineTransport([json.dumps({"type":"id","ok":True,"protocol_version":1,"role":role,"firmware_version":"0.1.0","board_id":board_id})])


def test_discovery_classifies_three_unique_device_roles():
    ports = {"COM4": make("dut","DUT-A"), "COM7": make("hil","HIL-B"), "COM9": make("witness","UNO")}
    found = discover_roles(ports)
    assert found["dut"].port == "COM4"
    assert found["hil"].port == "COM7"
    assert found["witness"].port == "COM9"
    assert all(t.writes == ["ID?"] for t in ports.values())


def test_discovery_rejects_duplicate_roles():
    ports = {"COM4": make("dut","A"), "COM7": make("dut","B")}
    with pytest.raises(DiscoveryError, match="duplicate role"):
        discover_roles(ports)


def test_discovery_rejects_incompatible_protocol_version():
    line = json.dumps({"type":"id","ok":True,"protocol_version":2,"role":"dut","firmware_version":"0.1.0","board_id":"A"})
    with pytest.raises(DiscoveryError, match="protocol"):
        discover_roles({"COM4": MemoryLineTransport([line])})
