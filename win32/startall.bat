@echo off
title Open Toontown - Unified Launcher
cd /d %~dp0..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

rem Launch the unified launcher (starts Astron, UberDOG, AI and the game client
rem from this single window). The individual start_*_server.bat scripts remain
rem available for advanced/manual use.
"%PPYTHON_PATH%" -u win32\launcher.py
