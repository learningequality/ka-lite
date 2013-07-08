@echo off

cd kalite
set /p cronserverpid=<cronserver.pid
set /p runcherrypyserverpid=<runcherrypyserver.pid

taskkill /f /pid %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
tskill %cronserverpid% > nul 2>&1 && echo Cron server was stopped!

taskkill /f /pid %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
tskill %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
cd ..