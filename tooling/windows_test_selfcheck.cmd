@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0selfcheck.ps1"
set "taskExit=%errorlevel%"
pause
exit /b %taskExit%
