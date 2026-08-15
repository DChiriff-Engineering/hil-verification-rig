# Architecture

## Roles

- **Pico #1 — DUT:** embedded power/thermal supervisor.
- **Pico #2 — HIL:** real-time sensor/plant simulator and fault injector.
- **Arduino UNO Rev3 — witness:** independent read-only observation path.
- **Host PC:** Python/pytest test executive, evidence capture, analysis, reporting.

## Conceptual plant

```text
I_load[k+1] = f(enable_cmd, scripted_load)
T[k+1]      = T[k] + heating(I_load) - cooling(fan_cmd)
V_bus[k+1]  = source_voltage - droop(I_load)
```

Fault injection may override sensor values, frame timing, CRC/checksum, sequence number, or freshness.

## DUT state concept

`STARTUP → NORMAL → DERATE → FAULT → RECOVERY`

Detailed thresholds and dwell times will be frozen as requirements before implementation.
