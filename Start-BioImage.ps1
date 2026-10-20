# Start this checkout's current workbench, regardless of the caller's directory.
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Push-Location -LiteralPath $PSScriptRoot
try {
    & uv run --locked --no-sync --project $PSScriptRoot python -I (Join-Path $PSScriptRoot 'tooling/launch_workbench.py') @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
