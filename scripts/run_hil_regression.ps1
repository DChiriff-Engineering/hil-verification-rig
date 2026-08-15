$ErrorActionPreference = "Stop"
$python = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Run .\scripts\setup_windows.ps1 first." }
$env:HIL_RUN = "1"
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$resultDir = Join-Path "results/local" "physical_$stamp"
New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
& $python -m pytest -m hil tests/hardware -v --junitxml (Join-Path $resultDir "junit.xml")
$code = $LASTEXITCODE
Remove-Item Env:HIL_RUN -ErrorAction SilentlyContinue
if ($code -ne 0) { exit $code }
Write-Host "Physical HIL regression JUnit evidence: $resultDir"
