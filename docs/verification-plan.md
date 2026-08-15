# Verification Plan

## Test classes

- smoke / bench health;
- nominal behavior;
- boundary conditions;
- timing/reaction latency;
- communication corruption;
- fault injection;
- robustness / repeated cycling;
- regression;
- independent witness cross-check.

## Representative tests

- boot safe state;
- nominal closed loop;
- undervoltage boundary;
- overvoltage trip;
- persistent overcurrent;
- thermal derating;
- severe overtemperature;
- sensor timeout;
- bad CRC/checksum;
- frozen/repeated sequence;
- recovery dwell;
- measured fault reaction latency;
- rapid fault cycling;
- witness cross-check.

Every test will record stimulus, expected behavior, actual behavior, timestamps, firmware/version metadata, and evidence paths.
