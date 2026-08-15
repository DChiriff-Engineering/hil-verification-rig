$ErrorActionPreference = "Stop"
$hilrig = Join-Path $PWD ".venv\Scripts\hilrig.exe"
if (-not (Test-Path $hilrig)) { throw "Run .\scripts\setup_windows.ps1 first." }
& $hilrig discover
exit $LASTEXITCODE
