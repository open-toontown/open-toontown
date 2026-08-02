@echo off
title Open Toontown - Game Client
cd /d %~dp0..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
for /f "usebackq delims=" %%i in ("PPYTHON_PATH") do set "PPYTHON_PATH=%%i"

set LOGIN_TOKEN=dev

"%PPYTHON_PATH%" -m toontown.launcher.QuickStartLauncher
pause
