# Run the demo script in-process. No server needed.
Set-Location (Join-Path $PSScriptRoot "..")

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No .venv found. Run scripts\setup.ps1 first."
    exit 1
}
& $python -m notifications.demo
exit $LASTEXITCODE
