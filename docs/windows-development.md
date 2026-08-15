# Windows Development & Bring-Up

The project is designed to be operated from Windows PowerShell.

## 1. Host environment

Requirements:

- Windows 10 or 11;
- Python 3.11+;
- Git;
- three USB data cables;
- jumper wires;
- two Raspberry Pi Pico boards;
- one Arduino UNO Rev3.

From the repository root:

```powershell
.\scripts\setup_windows.ps1
.\scripts\run_software_regression.ps1
```

## 2. Pico toolchain

CI pins the firmware build to **Raspberry Pi Pico SDK 2.3.0**. For a local source build, install a compatible ARM embedded GCC/CMake toolchain and set:

```powershell
$env:PICO_SDK_PATH = "C:\path\to\pico-sdk"
.\scripts\build_firmware.ps1
```

The expected UF2 files are:

```text
firmware\dut_pico\build\hil_dut_pico.uf2
firmware\hil_pico\build\hil_plant_pico.uf2
```

A simpler first physical session can use the commit-specific UF2 artifacts produced by GitHub Actions, avoiding local compiler setup.

## 3. UNO build/upload

GitHub CI compiles `firmware/witness_uno/witness_uno.ino` for `arduino:avr:uno`. On Windows, upload the same sketch with Arduino IDE or Arduino CLI. The witness firmware only configures the Pico-connected channels as inputs.

## 4. Flash and label boards

Physically label the Picos **DUT** and **HIL** before wiring. Flash the corresponding UF2 to each board using BOOTSEL mass-storage mode or another verified Pico programming method.

## 5. USB identity smoke test

Connect all three USB data cables. Windows COM numbers may change between sessions, so do not hard-code them.

```powershell
.\scripts\discover_rig.ps1
```

Expected roles:

```text
dut:     COMx ...
hil:     COMy ...
witness: COMz ...
```

The exact COM values are not important; unique role/board identity is.

## 6. Wire only after identity works

With boards disconnected from USB power while wiring:

- HIL GP0 → DUT GP1;
- DUT GP10 → HIL GP10;
- DUT GP11 → HIL GP11;
- DUT GP10 → UNO A0 (observation only);
- DUT GP12 → UNO A1 (observation only);
- common ground among directly interconnected boards.

Never connect a UNO output or 5 V node to Pico GPIO.

## 7. Physical regression

After re-powering and confirming identities:

```powershell
.\scripts\run_hil_regression.ps1
```

This explicitly enables pytest tests marked `hil`; ordinary CI never sets that gate.

## 8. Evidence handling

Physical local results are written beneath `results/local/`, which Git ignores. Review them before deciding which curated evidence belongs in the public portfolio. A failure is not deleted merely because it is inconvenient; preserve the evidence needed for root cause.
