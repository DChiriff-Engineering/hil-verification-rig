# Requirements

Implementation and verification are tracked separately. A requirement can be implemented in source while physical verification remains open.

| ID | Requirement | Implementation | Current verification level |
|---|---|---|---|
| SYS-001 | DUT shall enter a defined safe state after reset. | Implemented | software reference; physical pending |
| COM-001 | DUT shall accept valid sensor frames at the specified update period. | Implemented | protocol/software; physical UART pending |
| COM-002 | DUT shall reject frames with invalid CRC. | Implemented | unit/software scenario |
| COM-003 | DUT shall detect stale/missing sensor data after the 250 ms budget. | Implemented | unit/software scenario |
| COM-004 | DUT shall detect repeated/backward sequence values while allowing forward gaps after rejected frames. | Implemented | unit/software scenario |
| MON-001 | DUT shall supervise bus voltage. | Implemented | UV/OV software scenarios |
| MON-002 | DUT shall supervise load current. | Implemented | overcurrent software scenario |
| MON-003 | DUT shall supervise temperature. | Implemented | thermal software scenarios |
| CTRL-001 | DUT shall assert ENABLE only in permitted operating states. | Implemented | software scenarios; GPIO pending |
| CTRL-002 | DUT shall increase cooling/derating command as severity increases. | Implemented | software scenario; physical PWM pending |
| FLT-001 | DUT shall enter FAULT for defined severe electrical/thermal conditions. | Implemented | software scenarios |
| FLT-002 | DUT shall fail safe on sensor timeout and repeated integrity failure. | Implemented | software scenarios |
| FLT-003 | DUT shall reject configured implausible sensor slew. | Implemented | software regression; physical fault injection pending |
| REC-001 | DUT shall recover only after 1000 ms continuously healthy conditions. | Implemented | software scenario |
| DIAG-001 | DUT shall publish machine-readable state/fault diagnostics. | Implemented | client/source contract; physical USB pending |
| TEST-001 | Automated framework shall save pass/fail evidence for every executed test. | Implemented | unit/CLI tests |
| TEST-002 | Every safety/control requirement shall map to at least one verification test. | Implemented | traceability unit test |
| TEST-003 | Framework shall preserve evidence sufficient to reproduce/diagnose failures. | Implemented baseline | non-overwrite/report tests; physical evidence pending |

## Frozen verification constants

| Constant | Value |
|---|---:|
| Sensor update period | 50 ms |
| UV derate threshold | `< 10,500 mV` |
| Recovery voltage floor | `>= 10,800 mV` |
| OV fault threshold | `>= 14,500 mV` |
| Current warning/derate | `>= 4,500 mA` |
| Severe current threshold | `>= 6,000 mA` |
| Severe-current persistence | 3 valid frames |
| Thermal derate threshold | `>= 7,000 centi-C` |
| Severe temperature threshold | `>= 8,500 centi-C` |
| Missing sensor timeout | `> 250 ms` |
| Healthy recovery dwell | 1,000 ms |
| Corrupt/stale escalation | 3 consecutive frames |

These constants are intentionally testable model values and do not represent certified hardware limits.
