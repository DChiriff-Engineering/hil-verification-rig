from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Mapping

from .protocol import PROTOCOL_VERSION
from .transports import LineTransport, SerialLineTransport


class DiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    port: str
    role: str
    firmware_version: str
    board_id: str
    protocol_version: int


def discover_roles(ports: Mapping[str, LineTransport]) -> dict[str, DeviceIdentity]:
    found: dict[str, DeviceIdentity] = {}
    for port, transport in ports.items():
        transport.write_line("ID?")
        try:
            payload = json.loads(transport.read_line())
        except (json.JSONDecodeError, TimeoutError) as exc:
            raise DiscoveryError(f"{port}: invalid identity response") from exc
        if not payload.get("ok") or payload.get("type") != "id":
            raise DiscoveryError(f"{port}: identity response not OK")
        version = int(payload.get("protocol_version", -1))
        if version != PROTOCOL_VERSION:
            raise DiscoveryError(f"{port}: incompatible protocol version {version}")
        role = str(payload.get("role", ""))
        if role not in {"dut", "hil", "witness"}:
            raise DiscoveryError(f"{port}: unknown role {role!r}")
        if role in found:
            raise DiscoveryError(f"duplicate role {role}: {found[role].port} and {port}")
        found[role] = DeviceIdentity(
            port=port,
            role=role,
            firmware_version=str(payload.get("firmware_version", "unknown")),
            board_id=str(payload.get("board_id", "unknown")),
            protocol_version=version,
        )
    return found


def scan_system_ports(port_names: list[str] | None = None, *, transport_factory=None):
    """Probe candidate serial ports and return only recognized rig roles plus open transports."""
    if port_names is None:
        try:
            from serial.tools import list_ports
        except ImportError as exc:
            raise DiscoveryError("pySerial is required for system port discovery") from exc
        port_names = [port.device for port in list_ports.comports()]
    factory = transport_factory or (lambda port: SerialLineTransport(port))
    found: dict[str, DeviceIdentity] = {}
    kept: dict[str, LineTransport] = {}
    for port in port_names:
        transport = None
        try:
            transport = factory(port)
            one = discover_roles({port: transport})
            role, identity = next(iter(one.items()))
            if role in found:
                raise DiscoveryError(f"duplicate role {role}: {found[role].port} and {port}")
            found[role] = identity
            kept[role] = transport
        except DiscoveryError:
            if transport is not None:
                transport.close()
            continue
        except Exception:
            if transport is not None:
                transport.close()
            continue
    return found, kept
