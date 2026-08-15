# Requirements Traceability Matrix

| Requirement | Automated evidence | Physical evidence still required |
|---|---|---|
| SYS-001 | TC-001 + virtual DUT safe-state tests | DUT GPIO/USB state after real reset |
| COM-001 | TC-010 + frame encode/decode tests | physical UART traffic |
| COM-002 | TC-051 + CRC unit tests | corrupt-frame injection on real UART |
| COM-003 | TC-050 | measured physical timeout |
| COM-004 | TC-052 + isolated-CRC sequence-gap regression | repeated/frozen physical frames |
| MON-001 | TC-020, TC-021 | physical injected voltage-code response |
| MON-002 | TC-030 | physical current-code response |
| MON-003 | TC-040, TC-041 | physical thermal-code response |
| CTRL-001 | TC-001, TC-010, TC-020, TC-060 | ENABLE observed by HIL/UNO |
| CTRL-002 | TC-010, TC-040 | PWM observed by HIL |
| FLT-001 | TC-021, TC-030, TC-041, TC-070 | physical safe fault response |
| FLT-002 | TC-050, TC-051 | physical timeout/integrity response |
| FLT-003 | TC-052 + implausible-slew unit regression | optional physical slew injection |
| REC-001 | TC-060, TC-080 | physical dwell/repeated cycling |
| DIAG-001 | device-client tests + TC-021/TC-090 | DUT USB telemetry during physical tests |
| TEST-001 | evidence/CLI/JUnit tests + TC-080 | physical JUnit/result bundle |
| TEST-002 | `test_traceability.py` | review after final physical coverage additions |
| TEST-003 | evidence non-overwrite tests + TC-070/TC-090 infrastructure | retained physical logs/timestamps |

## Coverage gate

`tests/unit/test_traceability.py` fails if a scenario references an unknown requirement or if a safety/control requirement lacks scenario coverage. This matrix is the human-readable view of the same contract.
