( set /p cronserverpid=<cronserver.pid ) > nul 2>&1
taskkill /f /pid %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
tskill %cronserverpid% > nul 2>&1 && echo Cron server was stopped!
del cronserver.pid > nul 2>&1