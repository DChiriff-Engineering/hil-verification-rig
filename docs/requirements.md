# Requirements

| ID | Requirement | Status |
|---|---|---|
| SYS-001 | DUT shall enter a defined safe state after reset. | Planned |
| COM-001 | DUT shall accept valid sensor frames at the specified update period. | Planned |
| COM-002 | DUT shall reject frames with invalid checksum/CRC. | Planned |
| COM-003 | DUT shall detect stale or missing sensor data within the specified timeout. | Planned |
| MON-001 | DUT shall supervise bus voltage. | Planned |
| MON-002 | DUT shall supervise load current. | Planned |
| MON-003 | DUT shall supervise temperature. | Planned |
| CTRL-001 | DUT shall assert ENABLE only when operating conditions are valid. | Planned |
| CTRL-002 | DUT shall increase cooling/derating command as severity increases. | Planned |
| FLT-001 | DUT shall enter FAULT for defined severe electrical/thermal faults. | Planned |
| FLT-002 | DUT shall fail safe on sensor timeout. | Planned |
| REC-001 | DUT shall recover only after healthy conditions persist for the required dwell. | Planned |
| DIAG-001 | DUT shall publish machine-readable diagnostic state/fault reason. | Planned |
| TEST-001 | Automated framework shall save pass/fail evidence for every executed test. | Planned |
| TEST-002 | Every safety/control requirement shall map to at least one verification test. | Planned |
