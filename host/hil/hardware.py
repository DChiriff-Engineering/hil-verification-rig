from __future__ import annotations

from dataclasses import dataclass

from .devices import DutDevice, HilDevice, WitnessDevice
from .discovery import DeviceIdentity, DiscoveryError, scan_system_ports
from .transports import LineTransport


@dataclass(slots=True)
class PhysicalRig:
    identities: dict[str, DeviceIdentity]
    transports: dict[str, LineTransport]
    dut: DutDevice
    hil: HilDevice
    witness: WitnessDevice

    @classmethod
    def discover(cls) -> "PhysicalRig":
        identities, transports = scan_system_ports()
        missing = {"dut", "hil", "witness"} - set(identities)
        if missing:
            for transport in transports.values():
                transport.close()
            raise DiscoveryError(f"missing rig roles: {', '.join(sorted(missing))}")
        return cls(
            identities=identities,
            transports=transports,
            dut=DutDevice(transports["dut"]),
            hil=HilDevice(transports["hil"]),
            witness=WitnessDevice(transports["witness"]),
        )

    def close(self) -> None:
        for transport in self.transports.values():
            transport.close()
