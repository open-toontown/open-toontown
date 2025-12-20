@echo off
title Open Toontown - Astron Server
cd /d %~dp0..\astron\win32
astrond --loglevel info ../config/astrond.yml
pause
