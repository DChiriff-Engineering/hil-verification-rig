$ErrorActionPreference = "Stop"

if (-not $env:PICO_SDK_PATH) {
    throw "PICO_SDK_PATH is not set. Point it at a Raspberry Pi Pico SDK 2.3.0 checkout."
}
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    throw "cmake was not found in PATH."
}

cmake -S firmware/dut_pico -B firmware/dut_pico/build -DPICO_SDK_PATH="$env:PICO_SDK_PATH" -DPICO_BOARD=pico
cmake --build firmware/dut_pico/build --parallel 2
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

cmake -S firmware/hil_pico -B firmware/hil_pico/build -DPICO_SDK_PATH="$env:PICO_SDK_PATH" -DPICO_BOARD=pico
cmake --build firmware/hil_pico/build --parallel 2
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "DUT UF2: firmware\dut_pico\build\hil_dut_pico.uf2"
Write-Host "HIL UF2: firmware\hil_pico\build\hil_plant_pico.uf2"
