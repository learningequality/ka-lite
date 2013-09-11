rem have to change directory, in order to make sure we can access the pid file
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%\..\kalite"

( set /p runcherrypyserverpid=<runcherrypyserver.pid ) > nul 2>&1
taskkill /f /pid %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
tskill %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
del runcherrypyserver.pid > nul 2>&1

cd "%OLD_DIR%"