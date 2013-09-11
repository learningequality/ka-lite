rem have to change directory, in order to make sure we can access pid files
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%\..\kalite"

( set /p cronserverpid=<cronserver.pid ) > nul 2>&1
taskkill /f /pid %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
tskill %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
del cronserver.pid > nul 2>&1

cd "%OLD_DIR%"