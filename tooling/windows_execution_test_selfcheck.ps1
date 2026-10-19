# Explicit E7 dual-flow diagnostic; Windows PowerShell 5.1 compatible.
$ErrorActionPreference = 'Stop'
$taskRoot = Join-Path $env:LOCALAPPDATA 'BioImage-WB-E7-Test\Diagnostics'
New-Item -ItemType Directory -Path $taskRoot -Force | Out-Null
$taskExecutable = Join-Path $PSScriptRoot 'BioImageWB-Candidate.exe'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QPA_FONTDIR = Join-Path $env:SystemRoot 'Fonts'
$env:QTWEBENGINE_CHROMIUM_FLAGS = '--disable-gpu'
$env:PATH = Join-Path $env:SystemRoot 'System32'
Remove-Item Env:PYTHONPATH,Env:VIRTUAL_ENV,Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
try {
    foreach ($taskMode in @('--verify-installation', '--verify-intake-installation')) {
        $taskReport = Join-Path $taskRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N') + '.json')
        $taskProcess = Start-Process -FilePath $taskExecutable -ArgumentList @($taskMode, ('"' + $taskReport + '"')) -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput ($taskReport + '.stdout') -RedirectStandardError ($taskReport + '.stderr')
        if ($taskProcess.ExitCode -ne 0) { throw ($taskMode + ' exit code: ' + $taskProcess.ExitCode) }
        $taskData = Get-Content -LiteralPath $taskReport -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($taskData.phase -ne 'passed') { throw ($taskMode + ' report did not pass') }
        Write-Host ('PASS ' + $taskMode + ' - report: ' + $taskReport)
    }
    Write-Host 'Both engineering workflows passed. Scientific/clean Win10/DPI acceptance is separate.'
    exit 0
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message)
    Write-Host ('Keep reports/logs in: ' + $taskRoot)
    exit 1
}
