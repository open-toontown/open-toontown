@echo off
title OTP Server
cd ../otpgo

:main
"otpgo" config/otp.yml
pause
goto :main
