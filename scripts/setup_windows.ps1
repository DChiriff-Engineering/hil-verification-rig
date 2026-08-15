$ErrorActionPreference = "Stop"

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 -m venv .venv
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m venv .venv
} else {
    throw "Python 3.11+ was not found. Install Python, then rerun this script."
}

$python = Join-Path $PWD ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -e ".[dev]"
& $python -m pytest -m "not hil" -q

Write-Host ""
Write-Host "Host environment ready."
Write-Host "Next: .\scripts\discover_rig.ps1 after firmware is flashed and all three USB cables are connected."
