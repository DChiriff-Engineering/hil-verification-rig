# Test Results

## Automated hardware-independent verification

**Status:** PASS for the committed hardware-independent baseline.

GitHub Actions run **#2** (`31863961114`) on branch commit `9b8e0c6545464fe2a89878e2e19bf44f36562c4c` completed successfully.

| Verification item | Result |
|---|---|
| Host tests — Python 3.11 | **66 PASS; 6 physical tests deselected** |
| Host tests — Python 3.12 | **PASS** |
| Host tests — Python 3.13 | **PASS** |
| Python byte-compilation | **PASS** on all three matrix jobs |
| Deterministic TC-001…TC-090 software regression | **14 / 14 PASS** on all three matrix jobs |
| DUT Pico compiler gate | **PASS** |
| HIL Pico compiler gate | **PASS** |
| UNO Rev3 compiler gate | **PASS** |

The software suite includes the protocol/CRC contract, C/Python frame equivalence, deterministic plant/reference DUT, exact threshold and timing semantics, all fourteen approved core scenarios, traceability, role discovery, evidence/reporting, Windows/CI repository contracts, and hardware-test isolation.

## Firmware artifacts

Run #2 produced commit-specific artifacts:

- `hil-pico-firmware-9b8e0c6545464fe2a89878e2e19bf44f36562c4c`
  - `hil_dut_pico.uf2`
  - `hil_plant_pico.uf2`
  - `SHA256SUMS.txt`
- `hil-uno-witness-9b8e0c6545464fe2a89878e2e19bf44f36562c4c`
  - Arduino UNO compiled outputs
  - `SHA256SUMS.txt`

The downloaded artifact manifests were independently checked after CI: both UF2 files and all UNO build outputs matched their included SHA-256 checksums.

Compiler/artifact verification proves that the committed firmware is buildable with the configured toolchains. It does **not** prove board enumeration, electrical wiring, UART/GPIO/PWM behavior, reaction latency, or witness agreement.

## Physical HIL

_Not yet executed._

No physical UART, GPIO, PWM, timeout, reaction-latency, or UNO cross-check result is claimed here. Those results begin only after the three controllers are flashed, safely wired, discovered from Windows, and the hardware-marked pytest suite is run.
