# Safety & Usage

## Electrical invariant

The Arduino UNO Rev3 uses 5 V logic/power while Raspberry Pi Pico GPIO is 3.3 V. In this project's zero-cost baseline the UNO is **read-only** relative to Pico signals and must not drive Pico GPIO.

Safe baseline connections are Pico-to-Pico 3.3 V logic plus UNO analog observation of selected 0–3.3 V DUT outputs.

## Wiring order

1. Disconnect USB power before changing signal wiring.
2. Identify the DUT and HIL boards by label.
3. Connect common ground.
4. Connect Pico-to-Pico UART and DUT output observation lines.
5. Connect UNO A0/A1 observation wires only.
6. Inspect for accidental 5 V/VIN connections before powering.
7. Reconnect USB and run role discovery before running automated faults.

## Scope

This project simulates voltage/current/temperature in digital data. It does not switch real high power, certify a safety-critical controller, or create calibrated measurement equipment.

## Evidence safety

Do not represent software-model, CI compiler, or synthetic timing results as physical hardware validation. Physical claims require physical result bundles from the actual rig.
