@echo off
start "Starting Astron..." "start_astron_server.bat"
timeout /t 1 >nul
start "Starting UberDOG..." "start_uberdog_server.bat"
timeout /t 3 >nul
start "Starting AI..." "start_ai_server.bat"
timeout /t 3 >nul
start "Starting the game..." "start_game.bat"

rem Tip: create a new test account/toon with:
rem   ..\Panda3D\python\ppython.exe ..\tools\create_test_account.py --username test --toon-name "Test Toon"
