@echo off
title Open Toontown - Game Client
cd..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

rem TODO: Make this actually work, to change token in the meantime,
rem change the fake-playtoken variable in etc/Configrc.prc.
set LOGIN_TOKEN=dev

%PPYTHON_PATH% -m toontown.toonbase.ToontownStart
pause
