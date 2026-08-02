@echo off
title Open Toontown - Astron Server
cd /d %~dp0..

set "ASTROND="

rem 1) Prefer a bundled astrond.exe if you have one.
if exist "astron\win32\astrond.exe" set "ASTROND=astron\win32\astrond.exe"
if exist "astron\bin\astrond.exe" set "ASTROND=astron\bin\astrond.exe"
if exist "bin\astrond.exe" set "ASTROND=bin\astrond.exe"

rem 2) Otherwise, fall back to PATH.
if "%ASTROND%"=="" (
  where astrond >nul 2>nul
  if %errorlevel%==0 set "ASTROND=astrond"
)

if "%ASTROND%"=="" (
  echo.
  echo ERROR: Could not find astrond.exe.
  echo.
  echo Fix options:
  echo   - Install Astron and add astrond to PATH, then re-run this script.
  echo   - OR place astrond.exe at one of these paths:
  echo       astron\win32\astrond.exe
  echo       astron\bin\astrond.exe
  echo       bin\astrond.exe
  echo.
  pause
  exit /b 1
)

"%ASTROND%" --loglevel info astron/config/astrond.yml
pause
