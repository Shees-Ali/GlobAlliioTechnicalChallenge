# Start the app, then open http://127.0.0.1:8000/demo. Extra arguments go to uvicorn, for example: --port 8001
Set-Location (Join-Path $PSScriptRoot "..")

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "No .venv found. Run scripts\setup.ps1 first."
    exit 1
}
& $python -m uvicorn notifications.api.app:app @args
exit $LASTEXITCODE
