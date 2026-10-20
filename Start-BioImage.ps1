# Start this checkout's current workbench, regardless of the caller's directory.
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Push-Location -LiteralPath $PSScriptRoot
try {
    & uv run --locked --no-sync --project $PSScriptRoot python -m bioimage_app @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
