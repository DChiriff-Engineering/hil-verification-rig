$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$resultDir = Join-Path "results/local" "software_$stamp"
$hilrig = Join-Path $PWD ".venv\Scripts\hilrig.exe"
if (-not (Test-Path $hilrig)) { throw "Run .\scripts\setup_windows.ps1 first." }
& $hilrig software-regression --output $resultDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Software regression evidence: $resultDir"
