# Test Results

## Hardware-independent software verification

The local implementation has an automated pytest suite and deterministic software regression. Exact public pass counts are updated after the implementation branch is verified in GitHub Actions.

## Firmware compiler verification

_Pending first green GitHub Actions run of the committed implementation branch._

| Target | Toolchain | Result |
|---|---|---|
| DUT Pico | Raspberry Pi Pico SDK 2.3.0 / ARM GCC | Pending CI |
| HIL Pico | Raspberry Pi Pico SDK 2.3.0 / ARM GCC | Pending CI |
| UNO witness | Arduino CLI / `arduino:avr:uno` | Pending CI |

## Physical HIL

_Not yet executed._

No physical UART, GPIO, PWM, timeout, reaction-latency, or UNO cross-check result is claimed here yet.
