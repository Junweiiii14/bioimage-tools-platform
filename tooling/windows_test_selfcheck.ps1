# Windows PowerShell 5.1 is built into the supported Windows versions.
$ErrorActionPreference = 'Stop'
$taskRoot = Join-Path $env:LOCALAPPDATA 'BioImage-WB-Test\Diagnostics'
New-Item -ItemType Directory -Path $taskRoot -Force | Out-Null
$taskReport = Join-Path $taskRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N') + '.json')
$taskExecutable = Join-Path $PSScriptRoot 'BioImageWB-Candidate.exe'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QPA_FONTDIR = Join-Path $env:SystemRoot 'Fonts'
$env:QTWEBENGINE_CHROMIUM_FLAGS = '--disable-gpu'
$env:PATH = Join-Path $env:SystemRoot 'System32'
Remove-Item Env:PYTHONPATH,Env:VIRTUAL_ENV,Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
try {
    $taskProcess = Start-Process -FilePath $taskExecutable -ArgumentList @('--verify-installation', ('"' + $taskReport + '"')) -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput ($taskReport + '.stdout') -RedirectStandardError ($taskReport + '.stderr')
    if ($taskProcess.ExitCode -ne 0) { throw ('Self-check exit code: ' + $taskProcess.ExitCode) }
    $taskData = Get-Content -LiteralPath $taskReport -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($taskData.phase -ne 'passed') { throw 'Self-check report did not pass' }
    Write-Host 'PASS - offline runtime, OCR, quantification and project lifecycle checks passed.'
    Write-Host ('Report: ' + $taskReport)
    exit 0
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message)
    Write-Host ('Keep the report/logs and send them back: ' + $taskReport)
    exit 1
}
