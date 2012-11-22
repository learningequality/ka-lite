@echo off
echo.
echo Starting the cron server in the background.
start /B runhidden.vbs "python cronserver.py"