@echo off
title Open Toontown - UberDOG Server
cd /d %~dp0..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
for /f "usebackq delims=" %%i in ("PPYTHON_PATH") do set "PPYTHON_PATH=%%i"

"%PPYTHON_PATH%" -m toontown.uberdog.UDStart --base-channel 1000000 ^
               --max-channels 999999 --stateserver 4002 ^
               --messagedirector-ip 127.0.0.1:7199 ^
               --eventlogger-ip 127.0.0.1:7197
pause
