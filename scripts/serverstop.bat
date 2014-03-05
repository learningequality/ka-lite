@echo off

set "SCRIPT_DIR=%~dp0"
set "KALITE_DIR=%SCRIPT_DIR%..\kalite"

if exist "%KALITE_DIR%\runcherrypyserver.pid" (
    rem have to change directory, in order to make sure we can access the pid file
    set "CURRENT_DIR=%CD%"
    cd "%KALITE_DIR%"

    for /f "tokens=*" %%i in ( runcherrypyserver.pid ) do (
        taskkill /f /pid %%i > nul 2>&1 && echo CherryPy server was stopped!
        tskill %%i > nul 2>&1 && echo CherryPy server was stopped!
    )
    del runcherrypyserver.pid > nul 2>&1
    cd "%CURRENT_DIR%"
)