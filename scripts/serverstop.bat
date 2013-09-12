rem have to change directory, in order to make sure we can access the pid file
@echo off
set SCRIPT_DIR=%~dp0
set KALITE_DIR=%SCRIPT_DIR%\..\kalite

if exist "%KALITE_DIR%\runcherrypyserver.pid" (
  ( set /p runcherrypyserverpid=<"%KALITE_DIR%\runcherrypyserver.pid" ) > nul 2>&1
  taskkill /f /pid %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
  tskill %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
  del "%KALITE_DIR%\runcherrypyserver.pid" > nul 2>&1
)