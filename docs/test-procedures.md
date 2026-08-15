# Test Procedures

## Preconditions for any physical test

1. Use the commit-matched firmware artifacts from a green CI run or locally rebuilt equivalent.
2. Confirm the UNO has no output connection to either Pico.
3. Connect common ground before signal wires.
4. Connect HIL GP0 → DUT GP1 UART.
5. Connect DUT GP10 → HIL GP10 and DUT GP11 → HIL GP11.
6. Connect DUT GP10 → UNO A0 and DUT GP12 → UNO A1 for read-only witness observation.
7. Connect all three boards to the Windows host over USB data cables.
8. Run `scripts/discover_rig.ps1`; require one `dut`, one `hil`, and one `witness` identity.

## TC-001 — Boot safe state

- Reset DUT.
- Query `STATUS?` before relying on valid sensor frames.
- Require `STARTUP`, `enable=false`, and no unexplained fault.
- Cross-check ENABLE low at HIL and UNO where timing permits.

## TC-010 — Nominal closed loop

- Clear HIL injection.
- Set load to 2000 mA and source to 12000 mV.
- Reset DUT and allow at least 400 ms of valid frames.
- Require NORMAL or documented DERATE operation, ENABLE asserted, no fault, and plausible PWM observation.

## TC-020 — Undervoltage boundary

Exercise 10501, 10500, and 10499 mV (plus a broader sweep if useful). Verify equality remains outside the `<10500` derate criterion and below-threshold values enter DERATE.

## TC-021 — Overvoltage trip

Inject 14500 mV and a value above it. Verify immediate FAULT/disable and `OVERVOLTAGE` diagnostic reason.

## TC-030 — Overcurrent persistence

Inject 6000 mA for one, two, then three valid frames. Verify the first two frames do not produce the severe-current fault and the third does.

## TC-040 — Thermal derating

Use a **ramp**, not an impossible single jump, through the 70–85°C band. Record DUT PWM command and HIL measured PWM. Verify the command is monotonic with increasing thermal severity.

## TC-041 — Severe overtemperature

Cross 85.00°C with a controlled stimulus and verify safe fault/disable with the correct primary reason.

## TC-050 — Sensor timeout

Enable HIL dropout. Measure from the last valid sensor frame to the DUT fault/output response. Verify no premature timeout at the boundary and safe response after the budget.

## TC-051 — CRC corruption

- Corrupt one frame; verify rejection without permanent loss of sequence synchronization.
- Clear corruption and prove valid traffic continues.
- Corrupt three consecutive frames; verify escalation.

## TC-052 — Frozen/repeated sequence

Repeat/freeze frame sequence and verify stale counters and escalation according to the three-frame rule.

## TC-060 — Recovery dwell

After a fault, restore healthy conditions and verify ENABLE remains off through the full 1000 ms dwell. Verify recovery only after continuous health.

## TC-070 — Reaction latency

Timestamp fault injection in the HIL domain and capture the first observable safe DUT output transition. Preserve the raw timestamps and state whether the measurement is HIL-observed, DUT-reported, or UNO-observed.

## TC-080 — Repeated fault cycling

Repeat a representative fault/recovery sequence at least 20 times for portfolio closeout. Check state, counters, communication continuity, and unsafe transients.

## TC-090 — Independent witness cross-check

Compare DUT telemetry, HIL GPIO observation, and UNO observation. Define an allowed timestamp window from measured bench behavior. Preserve any discrepancy rather than deleting or averaging it away.
