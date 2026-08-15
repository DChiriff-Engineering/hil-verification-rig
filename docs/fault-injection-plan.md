# Fault Injection Plan

Faults are injected by the HIL Pico after the deterministic plant update and before the UART frame is emitted. The DUT firmware is never modified to create a test fault.

| Injection | HIL command | Effect | Target verification |
|---|---|---|---|
| undervoltage | `FAULT SET UNDERVOLTAGE <mV>` | override V_bus | TC-020 |
| overvoltage | `FAULT SET OVERVOLTAGE <mV>` | override V_bus | TC-021/TC-070 |
| overcurrent | `FAULT SET OVERCURRENT <mA>` | override I_load | TC-030 |
| overtemperature | `FAULT SET OVERTEMPERATURE <centi-C>` | override T | TC-040/TC-041 |
| CRC corruption | `FAULT SET BAD_CRC 1` | flip CRC byte | TC-051 |
| dropout | `FAULT SET DROPOUT 1` | suppress UART frames | TC-050 |
| repeated sequence | `FAULT SET REPEAT_SEQ 1` | hold sequence number | TC-052 |
| frozen frame | `FAULT SET FROZEN 1` | hold complete frame | TC-052 |

`FAULT CLEAR` removes the active override and returns to the live plant.

## Boundary discipline

Boundary tests should include **below / equal / above** values rather than only obviously safe/failing values. Timing tests similarly verify just-before and just-after the specified budget where practical.

## CRC/sequence interaction

An isolated bad CRC is intentionally rejected. The next valid forward sequence may skip the corrupted frame number and remains acceptable. Repeated or backward sequence values are invalid. This prevents a single deliberately corrupted frame from causing permanent false staleness.

## Plausibility priority

Implausible-slew detection is subordinate to primary severe fault classification. A severe overvoltage or overtemperature is still reported by its safety fault reason. Severe overcurrent retains the required persistence counter. Non-severe but physically implausible jumps may use `IMPLAUSIBLE_SLEW`.

## Deferred injectors

Seeded random noise, actuator-command mismatch, PIO-precise timing faults, long soak campaigns, and failover interfaces are stretch work after the deterministic core closes on hardware.
