@echo off
title Open Toontown - Freeze Capture
cd /d %~dp0..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
for /f "usebackq delims=" %%i in ("PPYTHON_PATH") do set "PPYTHON_PATH=%%i"

rem Enables shard breadcrumbs + watchdog stack dumps.
set TTBTN_FREEZE_CAPTURE=1

rem Default local dev login token (change as needed).
if "%LOGIN_TOKEN%"=="" set LOGIN_TOKEN=dev

"%PPYTHON_PATH%" -m toontown.launcher.QuickStartLauncher
echo.
echo If it freezes, in another window run:
echo   powershell -ExecutionPolicy Bypass -File win32\capture_hang_dump.ps1 -WaitSeconds 60 -DumpTag uberzone
echo For the newer post-setzone hang, use:
echo   powershell -ExecutionPolicy Bypass -File win32\capture_hang_dump.ps1 -WaitSeconds 30 -DumpTag postsetzone
pause

