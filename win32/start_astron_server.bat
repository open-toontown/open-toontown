@echo off
title Open Toontown - Astron Server
cd ../astron/win32
astrond --loglevel info ../config/astrond.yml
pause
