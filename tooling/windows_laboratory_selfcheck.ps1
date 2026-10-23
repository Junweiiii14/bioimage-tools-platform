# Windows PowerShell 5.1; private runtime, synthetic inputs and real process exits.
$ErrorActionPreference = 'Stop'
$taskRoot = Join-Path $env:LOCALAPPDATA 'BioImage-WB-Laboratory\Diagnostics'
New-Item -ItemType Directory -Path $taskRoot -Force | Out-Null
$taskExecutable = Join-Path $PSScriptRoot 'BioImageWB.exe'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QPA_FONTDIR = Join-Path $env:SystemRoot 'Fonts'
$env:QTWEBENGINE_CHROMIUM_FLAGS = '--disable-gpu'
$env:PATH = Join-Path $env:SystemRoot 'System32'
Remove-Item Env:PYTHONPATH,Env:VIRTUAL_ENV,Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
try {
    foreach ($taskMode in @('--verify-installation', '--verify-supervision-installation')) {
        $taskReport = Join-Path $taskRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N') + '.json')
        $taskProcess = Start-Process -FilePath $taskExecutable -ArgumentList @($taskMode, ('"' + $taskReport + '"')) -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru -RedirectStandardOutput ($taskReport + '.stdout') -RedirectStandardError ($taskReport + '.stderr')
        $null = $taskProcess.Handle
        if (-not $taskProcess.WaitForExit(180000)) { throw ($taskMode + ' timed out; process ' + $taskProcess.Id + '; keep report/logs') }
        if ($taskProcess.ExitCode -ne 0) { throw ($taskMode + ' exit code: ' + $taskProcess.ExitCode) }
        $taskData = Get-Content -LiteralPath $taskReport -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($taskData.phase -ne 'passed') { throw ($taskMode + ' report did not pass') }
        Write-Host ('PASS ' + $taskMode + ' - report: ' + $taskReport)
    }
    Write-Host 'PASS: local grayscale/OCR and crop/gray/results workflows. See reports for verification limits.'
    exit 0
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message)
    Write-Host ('Keep reports/logs in: ' + $taskRoot)
    exit 1
}
