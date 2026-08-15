# Three-Controller HIL Verification Bench for an Embedded Power/Thermal Supervisor

**Status:** Hardware-independent baseline verified in GitHub CI; physical Windows-rig validation remains pending.

A requirements-driven Hardware-in-the-Loop verification platform built from **two Raspberry Pi Pico boards**, an **Arduino UNO Rev3**, and a **Python/pytest** test executive. The bench verifies a physical embedded power/thermal supervisor against a deterministic real-time plant under nominal, boundary, timing, communication-fault, and safety-fault conditions.

> **Electrical safety invariant:** the Arduino UNO Rev3 is a 5 V board and is a **read-only witness** in this baseline. It must not drive Raspberry Pi Pico GPIO. Pico-to-Pico logic is 3.3 V.

## Why this project exists

The goal is not to emulate a commercial HIL rack or a real high-power converter. It is to demonstrate disciplined embedded verification engineering at portfolio scale:

- stable requirements and test IDs;
- physical DUT/HIL interfaces rather than software-only function calls;
- deterministic fault injection;
- C/C++ firmware plus Python automation;
- nominal, boundary, timing, robustness, and recovery testing;
- independent observation from a third controller;
- traceability and reproducible evidence;
- software-only CI plus firmware compiler gates;
- explicit separation between modeled evidence and measured physical results.

## Architecture

```text
Windows host PC
├── USB ──> Pico #1 DUT
├── USB ──> Pico #2 HIL plant / fault injector
└── USB ──> Arduino UNO Rev3 witness

Pico #2 GP0  ── 3.3 V UART sensor frames ──> Pico #1 GP1
Pico #1 GP10 ── ENABLE ────────────────────> Pico #2 GP10
Pico #1 GP11 ── fan / derating PWM ───────> Pico #2 GP11
Pico #1 GP10 ── status observation ───────> UNO A0 (input only)
Pico #1 GP12 ── FAULT observation ────────> UNO A1 (input only)

All directly interconnected boards share ground.
```

### Controller roles

**DUT Pico** implements a safety-oriented controller with states:

```text
STARTUP → NORMAL → DERATE → FAULT → RECOVERY
```

It validates versioned binary sensor frames, supervises voltage/current/temperature, rejects corrupt/stale data, detects timeout and implausible slew, drives physical ENABLE/PWM/status outputs, and publishes machine-readable USB diagnostics.

**HIL Pico** runs an intentionally simple deterministic plant:

```text
I_load[k+1] = enable ? scripted_load : 0
V_bus[k+1]  = source_voltage - I_load × droop
T[k+1]      = T[k] + heating(I_load) - cooling(PWM) - passive_cooling
```

It transmits real UART frames and can inject value overrides, CRC corruption, dropout, repeated sequence numbers, and frozen sensor behavior without modifying DUT firmware.

**UNO witness** only observes selected 0–3.3 V DUT outputs and timestamps independent measurements over USB.

## Frozen baseline thresholds

| Behavior | Baseline |
|---|---:|
| Sensor period | 50 ms |
| Undervoltage derate | `< 10,500 mV` |
| Recovery voltage floor | `>= 10,800 mV` |
| Overvoltage fault | `>= 14,500 mV` |
| Current derate | `>= 4,500 mA` |
| Severe overcurrent | `>= 6,000 mA` for 3 valid samples |
| Thermal derate | `>= 70.00 °C` |
| Severe overtemperature | `>= 85.00 °C` |
| Missing-data timeout | `> 250 ms` |
| Healthy recovery dwell | `1,000 ms` |
| Consecutive corrupt/stale escalation | 3 frames |

These are **verification model parameters**, not ratings for a real power product.

## Host software

The installable `hil` package contains:

- binary sensor protocol + CRC-16/CCITT-FALSE;
- deterministic plant/reference DUT models;
- approved TC-001…TC-090 scenario catalog;
- COM-port role discovery by firmware identity;
- DUT/HIL/witness clients using the same transport contract for real and fake devices;
- append-only evidence bundle generation;
- JUnit/CSV/Markdown reporting and plot helpers;
- physical rig discovery and pytest fixtures.

Run the software-only reference regression on Windows:

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_software_regression.ps1
```

Once the boards are flashed and wired:

```powershell
.\scripts\discover_rig.ps1
.\scripts\run_hil_regression.ps1
```

## Automated tests

The hardware-independent pytest suite covers protocol integrity, cross-language C/Python frame equivalence, exact threshold behavior, data-integrity escalation, timeout/recovery, deterministic plant response, all 14 approved core scenarios, traceability, COM discovery, evidence non-overwrite behavior, JUnit/report generation, and repository safety contracts.

Physical tests are marked `hil` and are skipped unless the Windows runner explicitly sets the hardware gate through `run_hil_regression.ps1`.

GitHub Actions is configured to build:

- host tests on Python 3.11 / 3.12 / 3.13;
- DUT Pico firmware against official Pico SDK 2.3.0;
- HIL Pico firmware against the same SDK;
- Arduino UNO Rev3 witness firmware with Arduino CLI;
- commit-specific firmware artifacts plus SHA-256 manifests.

## Evidence discipline

Software/reference-model results are labeled **software-simulation evidence**. They do not prove physical timing, GPIO levels, UART signal integrity, PWM measurement accuracy, or independent UNO agreement.

A physical run will create a timestamped folder under `results/local/` containing JUnit and raw evidence. Curated physical evidence is added to the public repository only after review.

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Interface Control Document](docs/interface-control-document.md)
- [Verification Plan](docs/verification-plan.md)
- [Requirements Traceability Matrix](docs/requirements-traceability-matrix.md)
- [Test Procedures](docs/test-procedures.md)
- [Fault Injection Plan](docs/fault-injection-plan.md)
- [Windows Development & Bring-Up](docs/windows-development.md)
- [Safety & Usage](docs/safety-and-usage.md)
- [Test Results](docs/test-results.md)
- [Final Verification Report](docs/final-verification-report.md)
- [Roadmap](ROADMAP.md)

## Results

**Host/software regression:** **PASS** — 66 hardware-independent tests under Python 3.11/3.12/3.13, plus the 14/14 deterministic core-scenario regression.

**Firmware compiler verification:** **PASS** — both RP2040 targets compile against Pico SDK 2.3.0 and the UNO witness compiles for `arduino:avr:uno`. Commit-matched artifacts are published by GitHub Actions with SHA-256 manifests.

**Physical HIL results:** _Not yet available._

**Measured reaction latency / witness agreement:** _Not yet available._

No physical result is inferred from simulation or compiler success.
