# HIL Verification Rig — Approved Design Specification

**Date:** 2026-08-14  
**Repository:** `DChiriff-Engineering/hil-verification-rig`  
**Status:** Approved design baseline; implementation pending  
**Host OS:** Windows  
**Available hardware:** 2× Raspberry Pi Pico, 1× Arduino UNO Rev3, 3× USB data cables, jumper wires

## 1. Objective

Build a professional three-controller Hardware-in-the-Loop verification bench that demonstrates requirements-driven embedded verification, fault injection, timing and boundary testing, traceability, regression, independent observation, and reproducible evidence.

The project verifies a physical embedded DC power/thermal subsystem supervisor without requiring hazardous or expensive power hardware.

## 2. Fixed Architecture

The hardware architecture is frozen:

- **Pico #1 — DUT:** fault-tolerant DC power/thermal subsystem supervisor.
- **Pico #2 — HIL plant/fault simulator:** deterministic plant, sensor-frame source, physical DUT-output observer, and fault injector.
- **Arduino UNO Rev3 — witness:** independent read-only observer/logger.
- **Windows host PC:** Python + pytest + pySerial test executive, evidence collector, and report generator.

```text
Windows host PC
├── USB → DUT Pico
├── USB → HIL Pico
└── USB → UNO witness

HIL Pico ── 3.3 V UART sensor frames ──> DUT Pico
DUT Pico ── ENABLE GPIO ──────────────> HIL Pico input
DUT Pico ── PWM command ──────────────> HIL Pico capture input
DUT Pico ── selected 0–3.3 V status ──> UNO analog/digital observation

Common ground for directly interconnected signals
```

## 3. Electrical Safety Rule

The UNO Rev3 is a 5 V board while Pico GPIO is 3.3 V. In the baseline design:

- the UNO **must never drive a Pico GPIO**;
- UNO-connected Pico status lines are observation-only;
- Pico-to-Pico logic remains direct 3.3 V with common ground;
- any future UNO-to-Pico active signal requires a separately validated level-shifting/interface design.

This rule is a project invariant, not an optional recommendation.

## 4. DUT Functional Design

The DUT receives periodic sensor frames containing:

- bus voltage;
- load current;
- system temperature;
- sequence number;
- CRC/checksum.

The controller validates integrity, sequence/freshness, timing, plausibility, and physical slew behavior where enabled.

### State model

```text
STARTUP → NORMAL → DERATE → FAULT → RECOVERY
```

Transitions are governed by sensor validity and protection thresholds. Severe faults fail safe. Recovery requires a healthy dwell interval rather than an immediate return to NORMAL.

### DUT outputs

- `ENABLE`: permission to energize the simulated load;
- PWM cooling/derating command;
- selected physical status GPIO outputs;
- machine-readable USB diagnostic telemetry.

### Protection behavior

The baseline shall implement:

- undervoltage supervision;
- overvoltage trip behavior;
- overcurrent persistence/trip behavior;
- high-temperature derating;
- severe overtemperature trip behavior;
- sensor timeout fail-safe;
- bad CRC/checksum rejection and escalation policy;
- repeated/stale sequence detection;
- frozen-sensor detection where configured;
- implausible-slew rejection where configured;
- recovery dwell;
- diagnostic counters for major error/fault classes.

Threshold constants and timing budgets shall be explicit, centralized, documented, and covered by boundary tests. They are engineering test parameters, not claims about a particular real power system.

## 5. HIL Plant and Fault-Injection Design

The HIL Pico maintains a deterministic simplified plant state:

```text
I_load[k+1] = f(enable_cmd, scripted_load)
T[k+1]      = T[k] + heating(I_load) - cooling(fan_cmd)
V_bus[k+1]  = source_voltage - droop(I_load)
```

The purpose is closed-loop testability, not physical-model fidelity. The equations and coefficients shall remain understandable, deterministic, and testable in both firmware and software simulation.

### HIL responsibilities

- capture DUT `ENABLE`;
- measure DUT PWM command sufficiently for the plant model and timing tests;
- advance the plant on a deterministic cadence;
- encode and transmit sensor frames over physical 3.3 V UART;
- receive host commands over USB serial;
- expose HIL telemetry and timestamps;
- execute deterministic fault injections.

### Fault catalog

The baseline fault API shall support:

- direct V/I/T value override;
- ramps across protection boundaries;
- severe step faults;
- controlled sensor-frame dropout;
- CRC/checksum corruption;
- repeated/skipped/corrupted sequence numbers;
- frozen sensor values;
- bounded deterministic noise;
- implausible slew;
- timing perturbation.

Actuator-command mismatch/failover, randomized fault campaigns, PIO timing capture, and soak tests remain stretch work until the core verification baseline is complete.

## 6. Sensor-Frame Protocol

A versioned binary Pico-to-Pico UART protocol shall be defined in the ICD and shared between DUT/HIL implementations.

The frame must provide, at minimum:

- synchronization/version information;
- sequence number;
- fixed-width bus voltage, load current, and temperature representations;
- integrity field (CRC/checksum);
- deterministic encoding/decoding rules.

The design shall prefer integer engineering units/fixed-point fields over floating-point transport so boundary behavior is deterministic across firmware and host models.

Malformed, corrupt, stale, and out-of-order frames must be testable without changing DUT code.

## 7. Independent UNO Witness

The UNO exists to create an independent evidence source rather than a second controller.

Baseline responsibilities:

- configure all Pico-connected witness pins strictly as inputs;
- observe selected 0–3.3 V DUT status signals;
- timestamp transitions/samples using the UNO's own clock domain;
- report observations over USB serial;
- never serve as the sole source of truth;
- enable host cross-checks among DUT telemetry, HIL observation, and independent witness evidence.

Disagreement among sources is retained as diagnostic evidence rather than silently reconciled.

## 8. Host Software Architecture

The Windows host package shall be structured around small explicit components:

- `transports.py` — line/binary serial framing, timeouts, and injected fake transports;
- `protocol.py` — typed protocol objects and integrity helpers;
- `dut.py` — DUT control/telemetry interface;
- `plant.py` — deterministic software reference plant;
- `hil_device.py` — HIL controller/fault API;
- `witness.py` — independent observer interface;
- `discovery.py` — COM-port probing and role/version identification;
- `scenarios.py` — reusable verification scenarios and boundary matrices;
- `evidence.py` / `reporting.py` — append-only run evidence and summaries;
- CLI entry point — discovery, smoke checks, individual scenarios, and full regression.

The API must work with physical serial transports and software fakes using the same behavioral contracts.

## 9. Verification Strategy

Verification is layered so software evidence is never confused with physical HIL evidence.

### Layer A — host/software unit tests

- protocol encode/decode and CRC;
- deterministic plant update equations;
- scenario expansion;
- boundary generation;
- evidence/report writing;
- device-role discovery through fake transports;
- timeout/error handling.

### Layer B — software-only system simulation

A deterministic virtual DUT/HIL transport validates orchestration and requirement logic in CI without hardware.

This layer covers representative:

- nominal closed loop;
- UV/OV boundaries;
- overcurrent persistence;
- thermal derating/severe thermal fault;
- timeout;
- corrupt frame;
- stale/frozen sequence;
- recovery dwell;
- repeated fault cycling;
- evidence-generation behavior.

It verifies framework/controller logic under modeled conditions only.

### Layer C — firmware build verification

GitHub Actions shall compile:

- DUT Pico firmware against an official pinned Raspberry Pi Pico SDK;
- HIL Pico firmware against the same SDK;
- UNO witness firmware with Arduino CLI/AVR core.

Compiler success is recorded separately from physical-board success.

### Layer D — physical HIL regression

Marked `pytest` hardware tests run only when the rig is attached. The physical suite verifies UART communication, GPIO/PWM feedback, timing, fault response, recovery, and witness agreement.

## 10. Core Verification Cases

The implementation shall provide explicit automated coverage for the approved test set:

- `TC-001` boot safe state;
- `TC-010` nominal closed loop;
- `TC-020` undervoltage boundary;
- `TC-021` overvoltage trip;
- `TC-030` overcurrent persistence;
- `TC-040` thermal derating;
- `TC-041` severe overtemperature;
- `TC-050` sensor timeout;
- `TC-051` bad CRC;
- `TC-052` frozen/repeated sensor sequence;
- `TC-060` recovery dwell;
- `TC-070` reaction-latency infrastructure;
- `TC-080` repeated fault cycling;
- `TC-090` independent witness cross-check.

Physical timing and cross-check results remain pending until hardware execution.

## 11. Requirements and Traceability

Stable IDs from the approved handoff remain authoritative, including `SYS-*`, `COM-*`, `MON-*`, `CTRL-*`, `FLT-*`, `REC-*`, `DIAG-*`, and `TEST-*` requirements.

The implementation will additionally restore omitted approved requirements such as sequence handling, implausible behavior where implemented, and raw-evidence preservation.

Every safety/control requirement must trace to at least one automated test. Traceability distinguishes:

- implementation status;
- software-simulation evidence;
- firmware-build evidence;
- physical-HIL evidence.

No requirement is labeled physically verified from CI alone.

## 12. Evidence Model

Each significant run gets a unique, timestamped, non-overwriting result directory such as:

```text
results/2026-08-XX_run-001/
├── metadata.json
├── requirements_snapshot.md
├── junit.xml
├── test_summary.csv
├── event_log.csv
├── dut_telemetry.csv
├── hil_telemetry.csv
├── witness_telemetry.csv
├── plots/
└── summary.md
```

Rules:

- existing evidence directories are never silently overwritten;
- failed tests preserve diagnostic evidence;
- metadata includes source/firmware versions where available;
- synthetic/software-only evidence is unmistakably labeled;
- plots answer a verification question rather than merely decorate the repository;
- final reports cite saved evidence rather than manually retyping measurements.

## 13. Windows Development Workflow

The repository shall document a Windows-first workflow using PowerShell commands where practical.

The developer setup will cover:

- Python virtual environment and editable host-package install;
- Raspberry Pi Pico C/C++ SDK/toolchain build procedure;
- Arduino CLI or Arduino IDE witness build/upload path;
- automatic COM-port role discovery;
- firmware build/flash steps;
- one-command software verification;
- one-command physical HIL regression once connected.

The repository must not assume a COM-port number is stable between sessions; discovery uses device identity responses instead.

## 14. CI/CD

Push/PR CI shall contain hardware-independent gates only:

1. Python unit/system-simulation tests;
2. experiment/scenario validation;
3. evidence/report-generation smoke test;
4. DUT Pico firmware compile;
5. HIL Pico firmware compile;
6. UNO witness firmware compile.

Generated local hardware results are not treated as CI evidence.

## 15. Scope Controls

### Must-have now

- DUT Pico firmware;
- HIL Pico plant/fault firmware;
- UNO read-only witness firmware;
- Python/pytest executive;
- versioned protocol and CRC/integrity logic;
- nominal, boundary, timing, corruption, timeout, electrical/thermal, and recovery test infrastructure;
- automated evidence/report generation;
- requirements traceability;
- software-only CI;
- compiler-verified firmware;
- Windows setup/bring-up instructions;
- professional README and final-report skeleton.

### Should-have when inexpensive and testable now

- reaction-latency measurement infrastructure;
- plots derived from evidence;
- repeatable regression command;
- UNO disagreement detection;
- bug-found-by-rig case-study template.

A bug case study is populated only if the rig genuinely exposes one.

### Deferred/stretch

- PIO deterministic capture;
- FMEA/FMECA;
- randomized fault campaigns;
- soak tests;
- GUI/dashboard;
- additional physical interfaces or failover;
- Project #7 FPGA integration.

## 16. Error-Handling Philosophy

Safety-relevant failures fail explicit and observable:

- malformed frames are rejected;
- missing/stale data drives defined fail-safe behavior;
- invalid host commands return structured errors;
- serial timeouts are bounded;
- fault state and reason are machine-readable;
- unexpected witness/HIL/DUT disagreement is recorded;
- report generation does not erase raw data;
- the host refuses incompatible protocol versions.

## 17. Completion Boundary for This Implementation Session

The hardware-independent baseline can be considered implemented only after fresh evidence shows:

- host/software tests pass;
- software-system scenarios pass;
- both Pico firmware targets compile in CI;
- UNO firmware compiles in CI;
- documentation/traceability are internally consistent;
- no license file is introduced;
- the repository makes no unearned physical-HIL claims.

Physical completion remains intentionally separate and requires the actual Windows rig:

- flash all three boards;
- confirm unique identities;
- wire common ground/UART/GPIO/PWM safely;
- run physical smoke test;
- run core HIL regression;
- measure reaction timing;
- run witness cross-check;
- preserve real result bundles;
- write final measured conclusions and recruiter/interview claims only from that evidence.

## 18. Non-Goals

This baseline does not attempt to create a research-grade electrical/thermal model, certify a safety-critical system, claim calibrated measurement accuracy, or emulate a commercial HIL rack. Its purpose is a rigorous portfolio-scale verification system with defensible interfaces, traceability, test automation, and evidence discipline.
