# Architecture

## System boundary

The project verifies a physical Raspberry Pi Pico DUT against a second Pico that acts as the simulated environment. An Arduino UNO Rev3 provides independent read-only observation, while a Windows host coordinates tests and records evidence.

```text
                     ┌───────────────────────────┐
                     │       Windows host        │
                     │ Python / pytest / pySerial│
                     └──────┬──────┬──────┬─────┘
                            │USB   │USB   │USB
                     ┌──────▼─┐ ┌──▼─────┐ ┌────▼─────┐
                     │ DUT Pico│ │HIL Pico│ │UNO witness│
                     └─┬─┬─┬──┘ └─┬──┬──┘ └──┬───────┘
                       │ │ │      │  │        │
 HIL GP0 ─UART────────>│ │ │      │  │        │
 DUT GP10 ENABLE ──────┘ │ └─────>│GP10       └─ A0 observe
 DUT GP11 PWM ───────────┘───────>│GP11
 DUT GP12 FAULT ───────────────────────────────> A1 observe
```

## Physical pin contract

| Signal | Source | Destination | Direction / voltage |
|---|---|---|---|
| Sensor UART | HIL GP0 | DUT GP1 | HIL → DUT, 3.3 V |
| ENABLE | DUT GP10 | HIL GP10 | DUT → HIL, 3.3 V |
| Fan/derate PWM | DUT GP11 | HIL GP11 | DUT → HIL, 3.3 V |
| ENABLE witness | DUT GP10 | UNO A0 | DUT → UNO input only, 0–3.3 V |
| FAULT witness | DUT GP12 | UNO A1 | DUT → UNO input only, 0–3.3 V |
| Ground | all interconnected boards | all | common reference |

The UNO is powered by USB and **must not drive** any Pico-connected signal in the baseline.

## DUT architecture

The DUT uses one main loop with bounded, non-blocking responsibilities:

1. collect bytes from UART and frame-align on `0xA55A`;
2. validate version and CRC;
3. validate sequence progression;
4. evaluate severe protections and plausibility;
5. update `STARTUP/NORMAL/DERATE/FAULT/RECOVERY` state;
6. update physical ENABLE, PWM, and FAULT outputs;
7. enforce missing-data timeout independently of new frames;
8. service non-blocking USB control/diagnostic commands;
9. publish periodic JSON telemetry.

Severe overvoltage and overtemperature have priority over plausibility classification. Severe overcurrent retains its defined three-valid-sample persistence requirement. Plausibility checks apply to non-severe jumps so they do not mask a primary severe safety fault.

## HIL Pico architecture

At a 50 ms cadence the HIL Pico:

1. samples DUT ENABLE;
2. derives PWM duty from GPIO edge timestamps;
3. advances the deterministic plant;
4. applies the active fault injector;
5. emits one binary sensor frame on UART;
6. publishes host-visible telemetry.

The plant uses integer arithmetic to keep the firmware and software reference model deterministic and explainable.

## UNO witness architecture

The UNO configures A0/A1 as inputs only, samples raw 10-bit ADC codes, derives coarse logic observations, timestamps with `millis()`, and reports JSON over USB. It does not participate in control.

## Host architecture

The Python package separates:

- wire protocol and CRC;
- deterministic reference models;
- scenario/requirements definitions;
- serial transport and role discovery;
- device clients;
- physical rig assembly;
- evidence/reporting;
- CLI commands.

Fake and physical transports obey the same line-oriented device-control contract, allowing CI to test orchestration without hardware.
