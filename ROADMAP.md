# Roadmap

## Phase 0 — Requirements / architecture / protocol

- [x] Freeze two-Pico + read-only UNO architecture.
- [x] Freeze Windows host workflow.
- [x] Define versioned sensor frame and CRC.
- [x] Freeze test thresholds and recovery policy.
- [x] Define physical pin map and electrical safety rule.

## Phase 1 — Hardware-independent host baseline

- [x] Protocol encoder/decoder and cross-language contract test.
- [x] Deterministic reference plant.
- [x] Reference DUT state/protection model.
- [x] TC-001…TC-090 software scenario catalog.
- [x] Requirements traceability model.
- [x] COM role discovery and device clients.
- [x] Non-overwriting evidence/JUnit/CSV/Markdown reporting.
- [x] Hardware tests isolated behind the `hil` marker.

## Phase 2 — Firmware baseline

- [x] DUT Pico firmware source.
- [x] HIL Pico plant/fault-injector firmware source.
- [x] Read-only UNO witness firmware source.
- [x] Local pin/safety/constant contract checks.
- [x] GitHub CI compiler verification for both Pico targets.
- [x] GitHub CI compiler verification for UNO Rev3.

## Phase 3 — Windows physical bring-up

- [x] PowerShell environment/build/discovery/regression scripts.
- [ ] Flash commit-matched DUT/HIL UF2 files.
- [ ] Flash commit-matched UNO witness firmware.
- [ ] Confirm three unique device identities.
- [ ] Wire common ground and HIL GP0 → DUT GP1 UART.
- [ ] Wire DUT ENABLE/PWM feedback to HIL.
- [ ] Wire DUT ENABLE/FAULT to UNO analog inputs only.
- [ ] Run safe-state and nominal physical smoke tests.

## Phase 4 — Core physical HIL verification

- [ ] TC-001 boot safe state.
- [ ] TC-010 nominal closed loop.
- [ ] TC-020 UV boundary.
- [ ] TC-021 OV fault.
- [ ] TC-030 overcurrent persistence.
- [ ] TC-040 thermal derating ramp.
- [ ] TC-041 severe overtemperature.
- [ ] TC-050 timeout.
- [ ] TC-051 CRC corruption.
- [ ] TC-052 repeated/frozen sensor behavior.
- [ ] TC-060 recovery dwell.
- [ ] TC-070 measured reaction latency.
- [ ] TC-080 repeated fault cycling.
- [ ] TC-090 UNO/HIL/DUT cross-check.

## Phase 5 — Evidence / portfolio closeout

- [ ] Preserve reviewed physical result bundles.
- [ ] Add plots from real evidence.
- [ ] Document any genuine bug found by the rig and its regression test.
- [ ] Complete final verification report.
- [ ] Record measured coverage and residual limitations.
- [ ] Capture wiring/bench photos and a short demo.
- [ ] Write resume bullet and interview story from actual measured results only.

## Stretch only after the core rig works

- [ ] RP2040 PIO timing capture.
- [ ] FMEA/FMECA table.
- [ ] Seeded randomized fault campaign.
- [ ] Long-duration soak test.
- [ ] GUI/dashboard.
- [ ] Additional interface/failover testing.
