# Run the test suite. Extra arguments go to pytest, for example: scripts\test.ps1 -q
Set-Location (Join-Path $PSScriptRoot "..")

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No .venv found. Run scripts\setup.ps1 first."
    exit 1
}
& $python -m pytest @args
exit $LASTEXITCODE
