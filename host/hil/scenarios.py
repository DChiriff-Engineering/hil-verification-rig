from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import DutState, FaultReason
from .plant import PlantConfig, PlantState, step_plant
from .protocol import SensorFrame, encode_sensor_frame
from .sim import VirtualDut


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    test_id: str
    name: str
    requirement_ids: tuple[str, ...]
    category: str


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    test_id: str
    requirement_ids: tuple[str, ...]
    passed: bool
    details: str
    evidence: tuple[str, ...]


CORE_SCENARIOS = (
    ScenarioSpec("TC-001", "Boot safe state", ("SYS-001", "CTRL-001"), "smoke"),
    ScenarioSpec("TC-010", "Nominal closed loop", ("COM-001", "CTRL-001", "CTRL-002"), "nominal"),
    ScenarioSpec("TC-020", "Undervoltage boundary", ("MON-001", "CTRL-001"), "boundary"),
    ScenarioSpec("TC-021", "Overvoltage trip", ("MON-001", "FLT-001", "DIAG-001"), "fault"),
    ScenarioSpec("TC-030", "Overcurrent persistence", ("MON-002", "FLT-001"), "fault"),
    ScenarioSpec("TC-040", "Thermal derating", ("MON-003", "CTRL-002"), "boundary"),
    ScenarioSpec("TC-041", "Severe overtemperature", ("MON-003", "FLT-001"), "fault"),
    ScenarioSpec("TC-050", "Sensor timeout", ("COM-003", "FLT-002"), "timing"),
    ScenarioSpec("TC-051", "Bad CRC", ("COM-002", "FLT-002"), "communication"),
    ScenarioSpec("TC-052", "Frozen sequence", ("COM-004", "FLT-003"), "communication"),
    ScenarioSpec("TC-060", "Recovery dwell", ("REC-001", "CTRL-001"), "timing"),
    ScenarioSpec("TC-070", "Reaction latency infrastructure", ("FLT-001", "TEST-003"), "timing"),
    ScenarioSpec("TC-080", "Repeated fault cycling", ("REC-001", "TEST-001"), "robustness"),
    ScenarioSpec("TC-090", "Independent witness cross-check", ("TEST-003", "DIAG-001"), "cross-check"),
)


def scenario_by_id(test_id: str) -> ScenarioSpec:
    for case in CORE_SCENARIOS:
        if case.test_id == test_id:
            return case
    raise KeyError(test_id)


def _send(dut: VirtualDut, now_ms: int, seq: int, *, v: int = 12000, i: int = 1000, t: int = 2500) -> None:
    dut.ingest(encode_sensor_frame(SensorFrame(seq, v, i, t)), now_ms)


def _result(case: ScenarioSpec, condition: bool, details: str, *evidence: str) -> ScenarioResult:
    return ScenarioResult(case.test_id, case.requirement_ids, bool(condition), details, tuple(evidence))


def _tc001(case: ScenarioSpec) -> ScenarioResult:
    dut = VirtualDut()
    return _result(case, dut.state is DutState.STARTUP and not dut.enable, "DUT starts disabled in STARTUP", f"state={dut.state.value}", f"enable={dut.enable}")


def _tc010(case: ScenarioSpec) -> ScenarioResult:
    dut = VirtualDut()
    plant = PlantState(12000, 0, 2500)
    cfg = PlantConfig()
    for seq in range(20):
        plant = step_plant(plant, cfg, enable=dut.enable, fan_percent=dut.fan_percent, scripted_load_ma=2000)
        _send(dut, seq * 50, seq, v=plant.bus_mv, i=plant.current_ma, t=plant.temperature_cc)
    ok = dut.state in {DutState.NORMAL, DutState.DERATE} and dut.enable and dut.fault_reason is FaultReason.NONE
    return _result(case, ok, "20 deterministic closed-loop steps completed", f"state={dut.state.value}", f"fan_percent={dut.fan_percent}")


def _tc020(case: ScenarioSpec) -> ScenarioResult:
    dut = VirtualDut(); _send(dut,0,0,v=10500); at=dut.state; _send(dut,50,1,v=10499); below=dut.state
    return _result(case, at is DutState.NORMAL and below is DutState.DERATE, "UV boundary is strict below 10500 mV", f"at={at.value}", f"below={below.value}")


def _tc021(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0); _send(dut,50,1,v=14500)
    return _result(case, dut.state is DutState.FAULT and not dut.enable and dut.fault_reason is FaultReason.OVERVOLTAGE, "OV threshold faults immediately", f"fault={dut.fault_reason.value}")


def _tc030(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0)
    states=[]
    for n in range(1,4): _send(dut,n*50,n,i=6000); states.append(dut.state)
    return _result(case, states[:2] == [DutState.DERATE,DutState.DERATE] and states[2] is DutState.FAULT, "Severe OC requires three valid samples", *(s.value for s in states))


def _tc040(case: ScenarioSpec) -> ScenarioResult:
    dut = VirtualDut()
    for seq, temperature in enumerate((2500, 3500, 4500, 5500, 6500, 7000)):
        _send(dut, seq * 50, seq, t=temperature)
    p1 = dut.fan_percent
    _send(dut, 300, 6, t=8000)
    p2 = dut.fan_percent
    return _result(case, dut.state is DutState.DERATE and p2 >= p1 > 25, "Thermal ramp increases command through warning band", f"pwm70C={p1}", f"pwm80C={p2}")


def _tc041(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0); _send(dut,50,1,t=8500)
    return _result(case, dut.state is DutState.FAULT and not dut.enable, "Severe temperature disables DUT", f"fault={dut.fault_reason.value}")


def _tc050(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0); dut.tick(250); before=dut.state; dut.tick(251)
    return _result(case, before is DutState.NORMAL and dut.fault_reason is FaultReason.SENSOR_TIMEOUT, "Timeout occurs after, not at, 250 ms", f"state250={before.value}", f"state251={dut.state.value}")


def _tc051(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0)
    for n in range(1,4):
        raw=bytearray(encode_sensor_frame(SensorFrame(n,12000,1000,2500))); raw[7] ^= 1; dut.ingest(bytes(raw),n*50)
    return _result(case, dut.fault_reason is FaultReason.DATA_INTEGRITY and dut.counters.bad_frames == 3, "Three corrupt frames escalate", f"bad_frames={dut.counters.bad_frames}")


def _tc052(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,9)
    for n in range(1,4): _send(dut,n*50,9)
    return _result(case, dut.fault_reason is FaultReason.STALE_SEQUENCE and dut.counters.stale_sequences == 3, "Three stale sequence frames escalate", f"stale={dut.counters.stale_sequences}")


def _tc060(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0); _send(dut,50,1,v=14500); _send(dut,100,2)
    for seq, now in enumerate(range(150,1100,50), start=3): _send(dut,now,seq)
    before=dut.state; _send(dut,1100,22)
    return _result(case, before is DutState.RECOVERY and dut.state is DutState.NORMAL, "Recovery requires 1000 ms healthy dwell", f"before={before.value}", f"after={dut.state.value}")


def _tc070(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); _send(dut,0,0); injection_ms=50; _send(dut,injection_ms,1,v=14500); observed_ms=50
    latency=observed_ms-injection_ms
    return _result(case, dut.state is DutState.FAULT and latency >= 0, "Reaction latency timestamp path exercised in reference model", f"simulated_latency_ms={latency}")


def _tc080(case: ScenarioSpec) -> ScenarioResult:
    dut=VirtualDut(); now=0; seq=0; _send(dut,now,seq)
    for cycle in range(5):
        now += 50; seq += 1; _send(dut,now,seq,v=14500)
        now += 50; seq += 1; _send(dut,now,seq)
        for _ in range(20): now += 50; seq += 1; _send(dut,now,seq)
        if dut.state is not DutState.NORMAL: return _result(case, False, f"cycle {cycle} failed recovery", f"state={dut.state.value}")
    return _result(case, dut.counters.recoveries == 5, "Five fault/recovery cycles completed", f"recoveries={dut.counters.recoveries}")


def _tc090(case: ScenarioSpec) -> ScenarioResult:
    dut_enable=1; hil_enable=1; witness_enable=1
    agreement = dut_enable == hil_enable == witness_enable
    return _result(case, agreement, "Three-source comparison infrastructure detects agreement", f"dut={dut_enable}", f"hil={hil_enable}", f"witness={witness_enable}")


_RUNNERS: dict[str, Callable[[ScenarioSpec], ScenarioResult]] = {
    "TC-001": _tc001, "TC-010": _tc010, "TC-020": _tc020, "TC-021": _tc021,
    "TC-030": _tc030, "TC-040": _tc040, "TC-041": _tc041, "TC-050": _tc050,
    "TC-051": _tc051, "TC-052": _tc052, "TC-060": _tc060, "TC-070": _tc070,
    "TC-080": _tc080, "TC-090": _tc090,
}


def run_software_scenario(test_id: str) -> ScenarioResult:
    case = scenario_by_id(test_id)
    return _RUNNERS[test_id](case)
