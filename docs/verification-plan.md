# Verification Plan

Verification is layered so compiler or simulation evidence is never represented as physical HIL evidence.

## Evidence levels

1. **Unit** — pure protocol/plant/controller/report behavior.
2. **Software system simulation** — approved scenarios against deterministic reference models.
3. **Cross-language contract** — host C compiler proves the shared C frame encoder matches Python byte-for-byte.
4. **Firmware compiler** — GitHub CI builds DUT Pico, HIL Pico, and UNO targets.
5. **Physical HIL** — real UART/GPIO/PWM behavior with the three connected boards.
6. **Independent witness** — UNO observation compared against HIL capture and DUT telemetry.

## Automated software suite

The default pytest run excludes hardware via the `hil` marker and covers:

- CRC standard vector and frame round-trip/corruption/version checks;
- Python/C frame byte equivalence;
- deterministic plant droop/heating/cooling behavior;
- exact UV, OV, OC, thermal, timeout, integrity, sequence, slew, and recovery behavior;
- isolated bad-CRC recovery without permanent sequence desynchronization;
- all 14 approved core scenario IDs;
- traceability integrity;
- fake COM role discovery and duplicate/incompatible-role handling;
- DUT/HIL/witness host clients;
- evidence non-overwrite behavior;
- JUnit/CSV/Markdown reporting;
- CI and repository safety contracts.

## Firmware compiler gates

GitHub Actions independently builds:

- `firmware/dut_pico` with official Pico SDK 2.3.0;
- `firmware/hil_pico` with the same SDK/toolchain;
- `firmware/witness_uno` for `arduino:avr:uno`.

Compiler success demonstrates source/toolchain compatibility only.

## Physical test matrix

| Test ID | Class | Stimulus | Primary acceptance evidence |
|---|---|---|---|
| TC-001 | smoke | reset/no sensors | STARTUP + ENABLE low |
| TC-010 | nominal | default plant/load | physical closed loop reaches NORMAL/DERATE without fault |
| TC-020 | boundary | V_bus sweep at 10,500 mV | equality/below behavior matches requirement |
| TC-021 | fault | 14,500+ mV | FAULT, ENABLE low, diagnostic reason |
| TC-030 | fault/timing | severe current for 1/2/3 frames | trip only at required persistence |
| TC-040 | boundary | plausible temperature ramp | monotonic derating response |
| TC-041 | fault | severe temperature | safe fault/disable |
| TC-050 | timing | frame dropout | fail safe after timeout budget |
| TC-051 | communication | isolated then repeated CRC corruption | isolated reject; repeated escalation |
| TC-052 | communication | repeat/freeze sequence | stale detection/escalation |
| TC-060 | timing | restore healthy sensors | no recovery before dwell |
| TC-070 | timing | timestamped severe fault | measured reaction latency retained, not estimated |
| TC-080 | robustness | repeated fault/recovery | no lockup/counter corruption/unsafe transient |
| TC-090 | cross-check | compare three sources | disagreement saved; agreement window reported |

## Physical evidence rules

- Hardware tests run only with the explicit Windows hardware gate.
- A failed test preserves raw output/JUnit rather than deleting it.
- Any measured latency is computed from retained timestamps.
- UNO/HIL/DUT discrepancies are evidence, not data to be silently reconciled.
- No result becomes a README claim until its associated raw evidence has been reviewed.
