# Thin Windows PowerShell 5.1 / PowerShell 7 entry; no installer execution.
param(
    [Parameter(Mandatory = $true)][string]$Python,
    [Parameter(Mandatory = $true)][string]$Candidate,
    [Parameter(Mandatory = $true)][string]$Installer,
    [Parameter(Mandatory = $true)][string]$InstallerSha256,
    [Parameter(Mandatory = $true)][string]$SourceCommit,
    [Parameter(Mandatory = $true)][string]$SourceRepo,
    [Parameter(Mandatory = $true)][string]$ReportDirectory,
    [string]$InstalledRoot = '',
    [string]$PreviousReport = '',
    [switch]$RunDiagnostics
)
$ErrorActionPreference = 'Stop'
# Do not inherit PS7 module paths into Windows PowerShell 5.1.
$env:PSModulePath = $PSHOME + '\Modules'
try {
    $taskReport = [IO.Path]::GetFullPath($ReportDirectory).TrimEnd('\', '/')
    if ([IO.Directory]::Exists($taskReport)) { throw 'Report directory already exists' }
    $taskRequest = @{
        command = 'verify'
        candidate = [IO.Path]::GetFullPath($Candidate)
        installer = [IO.Path]::GetFullPath($Installer)
        installer_sha256 = $InstallerSha256
        source_commit = $SourceCommit
        source_repo = [IO.Path]::GetFullPath($SourceRepo)
        report_directory = $taskReport
        powershell = @{ version = $PSVersionTable.PSVersion.ToString(); module_path = $env:PSModulePath }
    }
    if ($RunDiagnostics) { $taskRequest.command = 'run' }
    if ($InstalledRoot) { $taskRequest.installed_root = [IO.Path]::GetFullPath($InstalledRoot) }
    if ($PreviousReport) { $taskRequest.previous_report = [IO.Path]::GetFullPath($PreviousReport) }
    # Only the two regular file arguments cross the PS5.1 native boundary. Arbitrary
    # directory values (including trailing backslashes) remain JSON data.
    $taskRequestPath = [IO.Path]::Combine([IO.Path]::GetTempPath(), ('bioimage-acceptance-' + [guid]::NewGuid().ToString('N') + '.request.json'))
    $taskStream = [IO.File]::Open($taskRequestPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    $taskWriter = [IO.StreamWriter]::new($taskStream, [Text.UTF8Encoding]::new($false))
    try { $taskWriter.Write(($taskRequest | ConvertTo-Json -Depth 5)) } finally { $taskWriter.Dispose() }
    Write-Host ('Request retained: ' + $taskRequestPath)
    $taskScript = $PSScriptRoot + '\candidate_acceptance.py'
    & $Python -I -X utf8 $taskScript --request-file $taskRequestPath
    $taskExit = $LASTEXITCODE
    if ($null -eq $taskExit) { throw 'Verifier returned no process exit code' }
    exit $taskExit
} catch {
    Write-Error ('Candidate verification failed: ' + $_.Exception.Message) -ErrorAction Continue
    exit 1
}
