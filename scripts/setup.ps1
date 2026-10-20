# Create .venv with Python 3.12 or newer and install the project with its test dependencies.
Set-Location (Join-Path $PSScriptRoot "..")

$python = $null
foreach ($candidate in @("py -3", "python", "python3")) {
    $parts = $candidate.Split(" ")
    if (-not (Get-Command $parts[0] -ErrorAction SilentlyContinue)) { continue }
    $rest = @($parts | Select-Object -Skip 1)
    & $parts[0] @rest -c "import sys; sys.exit(sys.version_info < (3, 12))" 2>$null
    if ($LASTEXITCODE -eq 0) { $python = $parts; break }
}
if (-not $python) {
    Write-Host "Python 3.12 or newer is required. Install it, then run this script again."
    exit 1
}

$rest = @($python | Select-Object -Skip 1)
Write-Host "Using $(& $python[0] @rest --version)"
& $python[0] @rest -m venv .venv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Setup done. Next: scripts\test.ps1, scripts\demo.ps1 or scripts\run.ps1"
