@echo off
title Open Toontown - UberDOG Server
cd..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

%PPYTHON_PATH% -m toontown.uberdog.Start
pause
