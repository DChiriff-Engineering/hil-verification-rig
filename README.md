# Hardware-in-the-Loop Automated Verification Rig

**Status:** Planned — requirements and architecture established; implementation has not started.

A requirements-driven HIL verification bench using two Raspberry Pi Pico RP2040 boards, an Arduino UNO Rev3, and a Python/pytest host. The project is designed to validate an embedded power/thermal supervisor under nominal, boundary, timing, communication-fault, and safety-fault conditions.

> The UNO Rev3 is a 5 V board. In the zero-cost baseline it is a **read-only witness** and must not drive Pico GPIO directly.

## Architecture

```text
Host PC
├── USB → Pico #1 DUT
├── USB → Pico #2 HIL plant/fault simulator
└── USB → Arduino UNO witness

Pico #2 ── 3.3 V UART ──> Pico #1
Pico #1 ── ENABLE / PWM ──> Pico #2 inputs
Pico #1 ── selected 0–3.3 V status ──> UNO read-only observation
```

## Intended Engineering Signal

Embedded C/C++ · Python/pytest · physical HIL · fault injection · timing verification · requirements traceability · regression · reproducible evidence

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Interface Control Document](docs/interface-control-document.md)
- [Verification Plan](docs/verification-plan.md)
- [Fault Injection Plan](docs/fault-injection-plan.md)
- [Traceability Matrix](docs/requirements-traceability-matrix.md)
- [Roadmap](ROADMAP.md)

## Results

_Not yet available._
