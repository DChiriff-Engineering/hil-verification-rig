# Final Verification Report

**Status:** report structure prepared; physical verification results pending.

## 1. Configuration under test

Record:

- repository commit SHA;
- DUT firmware SHA/version/board ID;
- HIL firmware SHA/version/board ID;
- UNO firmware/version;
- Windows/Python/tool versions;
- wiring revision and photo reference.

## 2. Requirements coverage

Populate from the reviewed traceability matrix and executed JUnit/result bundle. Distinguish software-only from physical evidence.

## 3. Physical test summary

| Test ID | Result | Evidence bundle | Notes |
|---|---|---|---|
| TC-001 | Pending | — | boot safe state |
| TC-010 | Pending | — | nominal closed loop |
| TC-020 | Pending | — | UV boundary |
| TC-021 | Pending | — | OV fault |
| TC-030 | Pending | — | OC persistence |
| TC-040 | Pending | — | thermal derating |
| TC-041 | Pending | — | severe temperature |
| TC-050 | Pending | — | timeout |
| TC-051 | Pending | — | CRC behavior |
| TC-052 | Pending | — | stale/frozen sensor |
| TC-060 | Pending | — | recovery dwell |
| TC-070 | Pending | — | reaction latency |
| TC-080 | Pending | — | cycling/robustness |
| TC-090 | Pending | — | independent witness |

## 4. Timing results

Report measured timing only. Include measurement source, resolution, number of repetitions, min/median/max where useful, and retained raw timestamps.

## 5. Defects found by the rig

Populate only if a genuine DUT/HIL/framework defect is discovered. Record symptom, requirement/test that exposed it, root cause, fix commit, and regression test. Do not invent a case study.

## 6. Residual limitations

At minimum address:

- deterministic simplified plant rather than a calibrated physical plant;
- USB/host scheduling is not a hard real-time reference;
- UNO witness ADC uses its own 5 V-domain ADC/reference and is a coarse independent observer, not a precision instrument;
- baseline PWM timing uses GPIO edge timestamps on the HIL Pico rather than PIO capture;
- results apply to the tested firmware/configuration only.

## 7. Conclusion

Write only from executed evidence. The portfolio conclusion should emphasize requirements-driven verification, physical fault injection, traceability, repeatability, and defects/limitations actually observed.
