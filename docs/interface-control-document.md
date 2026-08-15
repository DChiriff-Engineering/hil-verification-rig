# Interface Control Document

## Electrical rules

- Pico-to-Pico logic is 3.3 V.
- Common ground is required for directly connected signals.
- Arduino UNO Rev3 is 5 V logic and is read-only in the baseline.
- No UNO digital output may directly drive a Pico GPIO without proper level shifting.

## Planned physical interfaces

| Interface | Source | Destination | Purpose |
|---|---|---|---|
| UART sensor frames | HIL Pico | DUT Pico | V/I/T sensor data + sequence + integrity field |
| ENABLE | DUT Pico | HIL Pico | Physical actuator-permission feedback |
| PWM command | DUT Pico | HIL Pico | Cooling/derating command |
| Status observation | DUT Pico | UNO analog/read-only input | Independent witness |
| USB serial | all boards | Host PC | Control, diagnostics, evidence |
