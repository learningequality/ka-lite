@echo off

rem have to change directory, in order to make sure we can access pid files
set SCRIPT_DIR=%~dp0
set KALITE_DIR=%SCRIPT_DIR%\..\kalite

( set /p cronserverpid=<"%KALITE_DIR%\cronserver.pid" ) > nul 2>&1
taskkill /f /pid %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
tskill %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
del "%KALITE_DIR%\cronserver.pid" > nul 2>&1

